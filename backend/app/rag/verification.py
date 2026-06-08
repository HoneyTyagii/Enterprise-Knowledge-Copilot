from __future__ import annotations

from typing import Any, Dict, List

from app.rag.citations import build_citation_map


def build_citations_and_grounding(retrieved_chunks: List[dict[str, Any]]) -> dict[str, Any]:
    """Placeholder grounding output.

    Later commits will: (1) call an LLM verifier, (2) enforce abstain/refuse,
    (3) attach citations to the final answer.
    """

    citations = build_citation_map(retrieved_chunks)

    return {
        "citations": [c.__dict__ for c in citations],
        "grounded": len(retrieved_chunks) > 0,
        "retrieved_count": len(retrieved_chunks),
    }

