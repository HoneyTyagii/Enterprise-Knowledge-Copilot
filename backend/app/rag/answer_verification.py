from __future__ import annotations

from typing import Any, Dict, List

from app.rag.schemas import RetrievedChunk


def verify_answer_grounding(
    *,
    query: str,
    answer: str,
    retrieved_chunks: List[RetrievedChunk],
    min_support_chunks: int = 2,
) -> Dict[str, Any]:
    """Grounding/verification step (placeholder).

    Production approach:
    - LLM verifier / entailment model that checks each claim against citations.
    - Compute grounding confidence.
    - Return verdict with abstain/refuse policy.

    Current placeholder heuristic:
    - If we have at least `min_support_chunks` retrieved chunks, consider grounded.
    """

    grounded = len(retrieved_chunks) >= min_support_chunks

    return {
        "grounded": grounded,
        "retrieved_support": len(retrieved_chunks),
        "verification_method": "heuristic_retrieval_count",
        "reason": "Not enough supporting chunks" if not grounded else "Sufficient supporting chunks retrieved",
    }


def apply_abstain_policy(
    *,
    verification_result: Dict[str, Any],
    answer: str,
    refuse_message: str = "I can’t answer that from the available sources.",
) -> Dict[str, Any]:
    if verification_result.get("grounded") is True:
        return {"final_answer": answer, "verdict": "grounded"}

    return {"final_answer": refuse_message, "verdict": "ungrounded"}

