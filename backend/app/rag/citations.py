from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass(frozen=True)
class Citation:
    citation_id: str
    document_id: int
    version_id: int
    chunk_index: int
    score: float
    location: str | None


def chunk_to_citation(
    *,
    chunk: dict[str, Any],
    citation_id: str | None = None,
    location: str | None = None,
) -> Citation: 
    cid = citation_id or f"doc{chunk['document_id']}:v{chunk['version_id']}:c{chunk['chunk_index']}"
    return Citation(
        citation_id=cid,
        document_id=int(chunk["document_id"]),
        version_id=int(chunk["version_id"]),
        chunk_index=int(chunk["chunk_index"]),
        score=float(chunk.get("hybrid_score", chunk.get("vector_similarity", 0.0))),
        location=location,
    )


def build_citation_map(retrieved_chunks: Iterable[dict[str, Any]]) -> List[Citation]:
    out: List[Citation] = []
    for i, chunk in enumerate(retrieved_chunks):
        out.append(
            chunk_to_citation(
                chunk=chunk,
                citation_id=f"[{i+1}]",
            )
        )
    return out

