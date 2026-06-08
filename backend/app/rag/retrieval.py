from __future__ import annotations

from typing import Any, List, Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.rag.embeddings import embed_texts


def _keyword_score(text: str, query: str) -> float:
    # Very small keyword scorer: counts token overlap.
    # Replace with postgres FTS/BM25 later.
    q = {t.lower() for t in query.split() if t.strip()}
    if not q:
        return 0.0

    tt = text.lower()
    hits = 0
    for term in q:
        if term in tt:
            hits += 1
    return float(hits) / float(len(q))


async def hybrid_retrieve(
    db: Session,
    *,
    workspace_id: int,
    query: str,
    limit: int = 10,
    alpha: float = 0.5,
) -> List[dict[str, Any]]:
    """Hybrid retrieval: vector similarity + lightweight keyword scoring.

    Note: For production, swap keyword scorer to a proper BM25/FTS.
    """

    # 1) Dense retrieval from pgvector
    embedding = (await embed_texts([query]))[0]
    embedding_literal = "[" + ",".join(str(x) for x in embedding) + "]"

    # Use `embedding <=> query_embedding` distance operator.
    # This uses exact operator; adjust for pgvector version.
    # We retrieve more than needed, then rerank with hybrid scoring.
    dense_rows = db.execute(
        text(
            """
            SELECT document_id, version_id, chunk_index, metadata_json,
                   (embedding <=> CAST(:embedding AS vector(256))) AS distance
            FROM document_vectors
            WHERE workspace_id = :workspace_id
            ORDER BY distance ASC
            LIMIT :dense_limit
            """
        ),
        {
            "embedding": embedding_literal,
            "workspace_id": workspace_id,
            "dense_limit": max(limit * 5, 20),
        },
    ).mappings().all()

    # 2) Keyword scoring against stored content is not present in vectors table.
    # We approximate by using metadata_json if it includes text; later we will join document_chunks.
    # Current ingestion stores chunk content in document_chunks, so do a join for candidates.
    candidate_chunk_keys: List[tuple[int, int, int]] = [
        (int(r["document_id"]), int(r["version_id"]), int(r["chunk_index"])) for r in dense_rows
    ]

    # Batch fetch chunk contents to score keywords
    if not candidate_chunk_keys:
        return []

    # Build a VALUES list for portability
    values_sql = ",".join(["(:d{},:v{},:c{})".format(i, i, i) for i in range(len(candidate_chunk_keys))])
    params: dict[str, Any] = {"workspace_id": workspace_id, "limit": limit}
    for i, (d_id, v_id, c_idx) in enumerate(candidate_chunk_keys):
        params[f"d{i}"] = d_id
        params[f"v{i}"] = v_id
        params[f"c{i}"] = c_idx

    rows = db.execute(
        text(
            f"""
            WITH cand(document_id, version_id, chunk_index) AS (
              VALUES {values_sql}
            )
            SELECT dc.document_id, dv.version_id, dc.chunk_index, dc.content
            FROM cand
            JOIN document_versions dv ON dv.document_id = cand.document_id AND dv.id = cand.version_id
            JOIN document_chunks dc ON dc.document_id = cand.document_id AND dc.chunk_index = cand.chunk_index
            WHERE dv.id IN (SELECT version_id FROM cand)
            LIMIT :limit
            """
        ),
        {**params, "limit": max(len(candidate_chunk_keys), limit * 5)},
    ).mappings().all()

    content_by_key = {(int(r["document_id"]), int(r["version_id"]), int(r["chunk_index"])): str(r["content"]) for r in rows}

    # 3) Combine scores
    results: List[dict[str, Any]] = []
    for r in dense_rows:
        d_id = int(r["document_id"])
        v_id = int(r["version_id"])
        c_idx = int(r["chunk_index"])
        distance = float(r["distance"])

        keyword_text = content_by_key.get((d_id, v_id, c_idx), "")
        k_score = _keyword_score(keyword_text, query)

        # Convert distance to similarity. Larger is better.
        # Similarity = 1/(1+distance)
        v_sim = 1.0 / (1.0 + distance)

        hybrid = alpha * v_sim + (1.0 - alpha) * k_score

        results.append(
            {
                "document_id": d_id,
                "version_id": v_id,
                "chunk_index": c_idx,
                "metadata_json": r.get("metadata_json") or {},
                "distance": distance,
                "keyword_score": k_score,
                "vector_similarity": v_sim,
                "hybrid_score": hybrid,
                "content": keyword_text,
            }
        )

    results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return results[:limit]

