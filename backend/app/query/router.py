from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_jwt_credentials
from app.audit.logging import QueryAuditRecord, persist_query_audit
from app.ingestion.service import list_chunks, list_documents
from app.multitenancy.dependencies import require_tenant_context
from app.multitenancy.context import TenantContext
from app.rag.answer_verification import apply_abstain_policy, verify_answer_grounding
from app.rag.citations import build_citation_map
from app.rag.pipeline import embed_and_upsert_document_chunks
from app.rag.qa import finalize_answer
from app.rag.rerank import rerank_chunks
from app.rag.retrieval import hybrid_retrieve
from app.rag.schemas import RetrievedChunk
from app.rbac.dependencies import require_permission
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/workspaces", tags=["query"])


def _retrieved_chunk(chunk: dict[str, Any], *, index: int) -> RetrievedChunk:
    return RetrievedChunk(
        document_id=int(chunk["document_id"]),
        version_id=int(chunk["version_id"]),
        chunk_index=int(chunk["chunk_index"]),
        content=str(chunk.get("content", "")),
        hybrid_score=float(chunk.get("hybrid_score", 0.0)),
        keyword_score=float(chunk.get("keyword_score", 0.0)),
        vector_similarity=float(chunk.get("vector_similarity", 0.0)),
        metadata_json=dict(chunk.get("metadata_json") or {}),
    )


@router.post("/{workspace_id}/query")
async def query_workspace(
    workspace_id: int,
    query: str,
    top_k: int = 5,
    ctx: TenantContext = Depends(require_permission("query", "document")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query must not be empty")

    documents = list_documents(db, workspace_id=workspace_id)
    if not documents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No documents in workspace")

    retrieved = await hybrid_retrieve(
        db,
        workspace_id=workspace_id,
        query=query,
        limit=max(top_k * 3, 15),
        alpha=0.7,
    )

    if not retrieved:
        return {
            "query": query,
            "answer": "I can't answer that from the available sources.",
            "verdict": "ungrounded",
            "citations": [],
            "retrieved_count": 0,
        }

    reranked = await rerank_chunks(query, [_retrieved_chunk(c, index=i) for i, c in enumerate(retrieved)], top_k=top_k)

    retrieved_chunks = [
        {
            "document_id": c.document_id,
            "version_id": c.version_id,
            "chunk_index": c.chunk_index,
            "content": c.content,
            "hybrid_score": c.hybrid_score,
        }
        for c in reranked
    ]

    citations = build_citation_map(retrieved)

    verification = verify_answer_grounding(
        query=query,
        answer=" ".join(c.content for c in reranked),
        retrieved_chunks=reranked,
    )
    applied = apply_abstain_policy(verification_result=verification)

    answer_text = applied["final_answer"]
    if applied["verdict"] == "ungrounded":
        answer_text = "I can't answer that from the available sources."

    commit = db
    try:
        persist_query_audit(
            commit,
            record=QueryAuditRecord(
                workspace_id=workspace_id,
                actor_id=str(ctx.actor_user_id),
                actor_email=ctx.actor_email,
                query_text=query,
                query_hash="",
                retrieved_chunk_ids_json="[]",
                draft_answer=answer_text,
                final_answer=answer_text,
                verdict=applied["verdict"],
                grounding_json="{}",
            ),
        )
    except Exception:
        pass

    return {
        "query": query,
        "answer": answer_text,
        "verdict": applied["verdict"],
        "citations": [c.__dict__ for c in citations],
        "retrieved_count": len(retrieved),
    }
