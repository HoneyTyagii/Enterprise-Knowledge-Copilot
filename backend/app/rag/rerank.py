from __future__ import annotations

from typing import List

from app.rag.schemas import RetrievedChunk


async def rerank_chunks(query: str, chunks: List[RetrievedChunk], top_k: int = 8) -> List[RetrievedChunk]:
    """Rerank placeholder.

    Replace with a cross-encoder/reranker model (e.g., Cohere rerank, sentence-transformers cross-encoder,
    or an LLM judge) in later commits.
    """

    # For now, keep order as produced by hybrid retrieval.
    return chunks[:top_k]

