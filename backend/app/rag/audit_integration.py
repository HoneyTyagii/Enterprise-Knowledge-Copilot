from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.audit.logging import QueryAuditRecord, persist_query_audit
from app.rag.schemas import RetrievedChunk


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def _retrieved_chunk_ids(chunks: List[RetrievedChunk]) -> List[str]:
    return [f"doc{c.document_id}:v{c.version_id}:c{c.chunk_index}" for c in chunks]


async def audit_query_and_answer(
    db: Session,
    *,
    workspace_id: int,
    actor_id: Optional[str],
    actor_email: Optional[str],
    query: str,
    retrieved_chunks: List[RetrievedChunk],
    draft_answer: str,
    final_answer: str,
    verdict: str,
    grounding: Dict[str, Any],
) -> None:
    record = QueryAuditRecord(
        workspace_id=workspace_id,
        actor_id=actor_id,
        actor_email=actor_email,
        query_text=query,
        query_hash=_hash_query(query),
        retrieved_chunk_ids_json=json.dumps(_retrieved_chunk_ids(retrieved_chunks)),
        draft_answer=draft_answer,
        final_answer=final_answer,
        verdict=verdict,
        grounding_json=json.dumps(grounding),
        created_at="",  # persist_query_audit will accept as-is in this scaffold
    )
    # Ensure created_at is filled if empty
    if not record.created_at:
        # persist_query_audit doesn't require it to be non-empty, but we keep format.
        # Recreate created_at here for correctness.
        from app.audit.logging import utc_now_iso

        record = QueryAuditRecord(
            **{**record.__dict__, "created_at": utc_now_iso()}
        )

    await persist_query_audit(db, record=record)

