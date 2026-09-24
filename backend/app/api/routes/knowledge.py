import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.api.dependencies import get_current_user
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.services.embedding_service import embedding_service
from app.schemas.knowledge import (
    DocumentCreate,
    DocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    SearchResultItem,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & RAG"])


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = KnowledgeRepository(db)
    doc = await repo.create(
        organization_id=current_user.organization_id,
        title=data.title,
        source_type=data.source_type or "text",
        source_url=data.source_url,
        metadata_json=data.metadata_json or {},
    )

    # Chunk and embed
    chunks = embedding_service.chunk_text(data.content)
    for c_text in chunks:
        emb = embedding_service.generate_embedding(c_text)
        await repo.add_chunk(
            organization_id=current_user.organization_id,
            document_id=doc.id,
            content=c_text,
            embedding=emb,
        )

    await db.commit()
    doc_with_chunks = await repo.get_with_chunks(doc.id, current_user.organization_id)
    return doc_with_chunks


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    data: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = KnowledgeRepository(db)
    query_emb = embedding_service.generate_embedding(data.query)

    chunks = await repo.vector_search(
        organization_id=current_user.organization_id,
        query_embedding=query_emb,
        top_k=data.top_k or 5,
    )

    results = [
        SearchResultItem(
            chunk_id=c.id,
            document_id=c.document_id,
            title=c.document.title if c.document else "Knowledge Document",
            content=c.content,
            score=0.94,
            metadata=c.metadata_json,
        )
        for c in chunks
    ]

    return KnowledgeSearchResponse(query=data.query, results=results)
