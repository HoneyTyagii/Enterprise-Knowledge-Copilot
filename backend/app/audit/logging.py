from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class QueryAuditRecord:
    workspace_id: int
    actor_id: Optional[str]
    actor_email: Optional[str]
    query_text: str
    query_hash: str
    retrieved_chunk_ids_json: str
    draft_answer: str
    final_answer: str
    verdict: str
    grounding_json: str
    created_at: str


async def persist_query_audit(
    db: Session,
    *,
    record: QueryAuditRecord,
) -> None:
    # Ensure table exists (migrations are expected in production).
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS query_audit_logs (
              id SERIAL PRIMARY KEY,
              workspace_id INTEGER NOT NULL,
              actor_id TEXT,
              actor_email TEXT,
              query_text TEXT NOT NULL,
              query_hash TEXT NOT NULL,
              retrieved_chunk_ids_json TEXT NOT NULL,
              draft_answer TEXT NOT NULL,
              final_answer TEXT NOT NULL,
              verdict TEXT NOT NULL,
              grounding_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
    )

    db.execute(
        text(
            """
            INSERT INTO query_audit_logs (
              workspace_id, actor_id, actor_email, query_text, query_hash,
              retrieved_chunk_ids_json, draft_answer, final_answer, verdict,
              grounding_json, created_at
            )
            VALUES (
              :workspace_id, :actor_id, :actor_email, :query_text, :query_hash,
              :retrieved_chunk_ids_json, :draft_answer, :final_answer, :verdict,
              :grounding_json, :created_at
            )
            """
        ),
        {
            "workspace_id": record.workspace_id,
            "actor_id": record.actor_id,
            "actor_email": record.actor_email,
            "query_text": record.query_text,
            "query_hash": record.query_hash,
            "retrieved_chunk_ids_json": record.retrieved_chunk_ids_json,
            "draft_answer": record.draft_answer,
            "final_answer": record.final_answer,
            "verdict": record.verdict,
            "grounding_json": record.grounding_json,
            "created_at": record.created_at,
        },
    )
    db.commit()


def make_audit_record(**kwargs: Any) -> QueryAuditRecord:
    return QueryAuditRecord(created_at=utc_now_iso(), **kwargs)

