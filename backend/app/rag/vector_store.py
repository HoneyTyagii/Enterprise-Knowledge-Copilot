from __future__ import annotations

from typing import Any, List, Sequence

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import settings


def _vector_table_name() -> str:
    return "document_vectors"


def ensure_vector_schema(session: Session) -> None:
    # pgvector extension + table. Safe-ish for local dev.
    # In production, manage with migrations.
    session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    session.commit()


def upsert_document_vectors(
    session: Session,
    *,
    workspace_id: int,
    document_id: int,
    version_id: int,
    chunk_rows: Sequence[dict[str, Any]],
    embeddings: Sequence[Sequence[float]],
) -> int:
    """Upsert vectors into pgvector.

    chunk_rows expected: [{chunk_index, content_fingerprint(optional), metadata_json(optional), ...}]

    Uses `vector` column and ON CONFLICT on (workspace_id, document_id, version_id, chunk_index).
    """

    ensure_vector_schema(session)

    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS document_vectors (
              id SERIAL PRIMARY KEY,
              workspace_id INTEGER NOT NULL,
              document_id INTEGER NOT NULL,
              version_id INTEGER NOT NULL,
              chunk_index INTEGER NOT NULL,
              embedding vector(256) NOT NULL,
              metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              UNIQUE(workspace_id, document_id, version_id, chunk_index)
            );
            """
        )
    )
    session.commit()

    table = _vector_table_name()

    # Build one insert per row (simple; optimize later)
    upserted = 0
    for row, emb in zip(chunk_rows, embeddings):
        payload = {
            "workspace_id": workspace_id,
            "document_id": document_id,
            "version_id": version_id,
            "chunk_index": int(row["chunk_index"]),
            "embedding": list(emb),
            "metadata_json": row.get("metadata_json", {}),
        }

        # pgvector expects string format like '[0.1,0.2]' when bound as text; simplest approach: cast.
        embedding_literal = "[" + ",".join(str(x) for x in payload["embedding"]) + "]"

        session.execute(
            text(
                f"""
                INSERT INTO {table} (workspace_id, document_id, version_id, chunk_index, embedding, metadata_json)
                VALUES (:workspace_id, :document_id, :version_id, :chunk_index, CAST(:embedding AS vector(256)), :metadata_json)
                ON CONFLICT (workspace_id, document_id, version_id, chunk_index)
                DO UPDATE SET
                  embedding = CAST(:embedding AS vector(256)),
                  metadata_json = :metadata_json
                """
            ),
            {
                **payload,
                "embedding": embedding_literal,
            },
        )
        upserted += 1

    session.commit()
    return upserted

