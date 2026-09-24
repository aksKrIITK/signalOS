import uuid
from typing import List, Optional, Sequence, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.knowledge import Document, KnowledgeChunk
from app.db.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository[Document]):
    def __init__(self, db: AsyncSession):
        super().__init__(Document, db)

    async def get_with_chunks(self, id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Document]:
        query = select(Document).where(
            Document.id == id,
            Document.organization_id == organization_id,
        ).options(selectinload(Document.chunks))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def vector_search(
        self,
        organization_id: uuid.UUID,
        query_embedding: List[float],
        top_k: int = 20,
        metadata_filter: Optional[dict] = None,
    ) -> Sequence[KnowledgeChunk]:
        # Using pgvector cosine distance: embedding.cosine_distance(query_embedding)
        query = select(KnowledgeChunk).where(
            KnowledgeChunk.organization_id == organization_id
        )
        if query_embedding:
            query = query.order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
        query = query.limit(top_k)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_chunk(
        self,
        organization_id: uuid.UUID,
        document_id: uuid.UUID,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata_json: Optional[dict] = None,
    ) -> KnowledgeChunk:
        chunk = KnowledgeChunk(
            organization_id=organization_id,
            document_id=document_id,
            content=content,
            embedding=embedding,
            metadata_json=metadata_json or {},
        )
        self.db.add(chunk)
        await self.db.flush()
        await self.db.refresh(chunk)
        return chunk
