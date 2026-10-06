import uuid
import structlog
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.db.models.knowledge import Document, KnowledgeChunk
from app.services.embedding_service import embedding_service
from app.llm.openai import OpenAIProvider
from app.llm.base import ChatMessage
from app.core.config import settings

logger = structlog.get_logger(__name__)


class RagPipelineService:
    """
    Production-Grade Retrieval-Augmented Generation (RAG) Pipeline.
    
    Architecture:
    1. Ingestion: Hierarchical semantic chunking + async batch embedding (1536-dim pgvector).
    2. Hybrid Retrieval: pgvector vector cosine similarity initial search (Top K=20).
    3. Reranking: Production Cross-Encoder / Cohere API / Hybrid RRF Reranking (Top N=5).
    4. Synthesis: Grounded context prompt construction + LLM answer synthesis with citations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.knowledge_repo = KnowledgeRepository(db)
        self.llm_provider = OpenAIProvider()

    async def ingest_document(
        self,
        organization_id: uuid.UUID,
        title: str,
        content: str,
        source_type: str = "text",
        source_url: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> Dict[str, Any]:
        """
        Ingests a raw document into the RAG pipeline.
        Chunks text semantically, generates vector embeddings in batch, and persists to DB.
        """
        if not content.strip():
            raise ValueError("Document content cannot be empty")

        # 1. Hierarchical Semantic Chunking
        chunks_text = embedding_service.chunk_text(
            text=content, chunk_size=chunk_size, overlap=overlap
        )
        if not chunks_text:
            chunks_text = [content]

        logger.info(
            "Ingesting document for RAG",
            organization_id=str(organization_id),
            title=title,
            num_chunks=len(chunks_text),
        )

        # 2. Async Batch Embeddings Generation
        embeddings = await embedding_service.generate_embeddings_batch_async(chunks_text)

        # 3. Create Document DB Record
        doc = Document(
            organization_id=organization_id,
            title=title,
            source_type=source_type,
            source_url=source_url,
            metadata_json=metadata_json or {},
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)

        # 4. Save Chunks with Embeddings
        chunk_records = []
        for idx, (chunk_t, emb) in enumerate(zip(chunks_text, embeddings)):
            c_meta = (metadata_json or {}).copy()
            c_meta["chunk_index"] = idx
            c_meta["total_chunks"] = len(chunks_text)

            chunk_obj = await self.knowledge_repo.add_chunk(
                organization_id=organization_id,
                document_id=doc.id,
                content=chunk_t,
                embedding=emb,
                metadata_json=c_meta,
            )
            chunk_records.append(chunk_obj)

        await self.db.commit()

        return {
            "document_id": str(doc.id),
            "title": doc.title,
            "chunks_created": len(chunk_records),
        }

    async def retrieve_context(
        self,
        organization_id: uuid.UUID,
        query: str,
        top_k: int = 20,
        rerank_top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant knowledge chunks for a query using 2-stage retrieval:
        Stage 1: pgvector Cosine Distance Vector Search (retrieves top_k candidates)
        Stage 2: Cross-Encoder / Cohere / Hybrid RRF Reranking (filters down to rerank_top_k)
        """
        # 1. Embed query vector
        query_embeddings = await embedding_service.generate_embeddings_batch_async([query])
        query_vector = query_embeddings[0] if query_embeddings else []

        # 2. Stage 1: Initial Vector Search in pgvector
        candidate_chunks = await self.knowledge_repo.vector_search(
            organization_id=organization_id,
            query_embedding=query_vector,
            top_k=top_k,
        )

        if not candidate_chunks:
            return []

        # Convert ORM chunks to dictionary candidates for reranker
        candidates_dict = []
        for chunk in candidate_chunks:
            candidates_dict.append({
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "content": chunk.content,
                "metadata": chunk.metadata_json,
            })

        # 3. Stage 2: Cross-Encoder / Hybrid Reranking
        reranked_chunks = await embedding_service.rerank_async(
            query=query,
            candidates=candidates_dict,
            top_k=rerank_top_k,
            text_key="content",
        )

        return reranked_chunks

    async def answer_query(
        self,
        organization_id: uuid.UUID,
        query: str,
        top_k: int = 20,
        rerank_top_k: int = 5,
        system_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end RAG pipeline:
        1. Context retrieval & reranking
        2. Grounded context formatting
        3. LLM answer generation with explicit source citations
        """
        retrieved_chunks = await self.retrieve_context(
            organization_id=organization_id,
            query=query,
            top_k=top_k,
            rerank_top_k=rerank_top_k,
        )

        if not retrieved_chunks:
            return {
                "answer": "No relevant context found in the knowledge base to answer your query.",
                "sources": [],
                "context_used": 0,
            }

        # Format context block with citations
        context_blocks = []
        sources = []
        for idx, item in enumerate(retrieved_chunks, 1):
            source_info = f"[Source {idx} - Chunk {item['chunk_id'][:8]}]"
            context_blocks.append(f"{source_info}:\n{item['content']}")
            sources.append({
                "source_id": idx,
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "rerank_score": item.get("rerank_score", 0.0),
            })

        formatted_context = "\n\n---\n\n".join(context_blocks)

        default_system = (
            "You are an expert AI Assistant operating inside SignalOS. "
            "Answer the user query accurately and concisely based ONLY on the provided Context Blocks. "
            "If the context does not contain enough information to answer, state clearly that you do not know. "
            "Cite sources where appropriate using [Source N]."
        )

        messages = [
            ChatMessage(role="system", content=system_instructions or default_system),
            ChatMessage(
                role="user",
                content=f"Context Blocks:\n{formatted_context}\n\nUser Question: {query}",
            ),
        ]

        # Call LLM Provider
        try:
            llm_response = await self.llm_provider.generate(
                messages=messages,
                temperature=0.2,
                max_tokens=1500,
            )
            answer_text = llm_response.content
        except Exception as e:
            logger.error("LLM Generation error during RAG", error=str(e))
            answer_text = f"Retrieved {len(retrieved_chunks)} relevant context blocks, but failed to synthesize LLM answer: {str(e)}"

        return {
            "answer": answer_text,
            "sources": sources,
            "context_chunks": retrieved_chunks,
            "context_used": len(retrieved_chunks),
        }
