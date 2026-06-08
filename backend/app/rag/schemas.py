from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    document_id: int
    version_id: int
    chunk_index: int
    content: str
    hybrid_score: float
    keyword_score: float
    vector_similarity: float
    metadata_json: dict[str, Any] = {}


class RerankResult(BaseModel):
    items: list[RetrievedChunk]
    model_used: Optional[str] = None

