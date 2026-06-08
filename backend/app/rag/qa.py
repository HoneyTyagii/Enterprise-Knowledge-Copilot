from __future__ import annotations

from typing import Any, Dict, List

from app.rag.answer_verification import apply_abstain_policy, verify_answer_grounding
from app.rag.schemas import RetrievedChunk


def finalize_answer(
    *,
    query: str,
    draft_answer: str,
    retrieved_chunks: List[RetrievedChunk],
) -> Dict[str, Any]:
    verification = verify_answer_grounding(
        query=query,
        answer=draft_answer,
        retrieved_chunks=retrieved_chunks,
    )
    applied = apply_abstain_policy(verification_result=verification, answer=draft_answer)

    return {
        "answer": applied["final_answer"],
        "verdict": applied["verdict"],
        "verification": verification,
    }

