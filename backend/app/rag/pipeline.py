from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy.orm import Session

from app.rag.embeddings import embed_texts
from app.rag.vector_store import upsert_document_vectors


async def embed_and_upsert_document_chunks(
    db: Session,
    *,
    workspace_id: int,
    document_id: int,
    version_id: int,
    chunks: Sequence[dict[str, Any]],
) -> int:
    """Embed chunk content and upsert into pgvector.

    `chunks` expects: [{chunk_index, content, metadata_json?, ...}]
    """

    texts = [str(c["content"]) for c in chunks]
    embeddings = await embed_texts(texts)

    chunk_rows = []
    for c in chunks:
        chunk_rows.append(
            {
                "chunk_index": c["chunk_index"],
                "metadata_json": c.get("metadata_json", {}),
            }
        )

    return upsert_document_vectors(
        db,
        workspace_id=workspace_id,
        document_id=document_id,
        version_id=version_id,
        chunk_rows=chunk_rows,
        embeddings=embeddings,
    )

