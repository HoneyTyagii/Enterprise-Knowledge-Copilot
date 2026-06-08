from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_rag_hybrid_retrieval_scoring_smoke():
    """Integration/unit skeleton.

    Goals:
    - query -> hybrid retrieval
    - ensure returned items include keyword_score/vector_similarity/hybrid_score
    - ensure ordering is by hybrid_score

    Implement with seeded document_chunks + pgvector embeddings in later commits.
    """

    # TODO: setup test db + seed vectors and chunks
    assert True

