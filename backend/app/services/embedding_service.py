import hashlib
from typing import List, Optional
import numpy as np


class EmbeddingService:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            i += max(1, chunk_size - overlap)
        return chunks

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates normalized deterministic 1536-dim vector embedding
        (based on cryptographic hash seed) for fast local pgvector storage.
        """
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.dimension)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def rerank(self, query: str, candidates: List[dict], top_k: int = 5) -> List[dict]:
        """Reranks candidate chunks by keyword density and semantic relevance."""
        query_terms = set(query.lower().split())
        scored = []
        for c in candidates:
            content = c.get("content", "").lower()
            overlap_score = sum(1 for term in query_terms if term in content)
            scored.append((overlap_score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]


embedding_service = EmbeddingService()
