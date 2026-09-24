import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    source_type: Optional[str] = "text"
    source_url: Optional[str] = None
    content: str
    metadata_json: Optional[Dict[str, Any]] = None


class KnowledgeChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    content: str
    metadata_json: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    source_type: str
    source_url: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    chunks: Optional[List[KnowledgeChunkResponse]] = None

    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    metadata_filter: Optional[Dict[str, Any]] = None


class SearchResultItem(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
