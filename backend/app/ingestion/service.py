import hashlib
import os
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.ingestion.schemas import IngestJobOut
from app.ingestion.versions import DocumentVersion
from app.rag.embeddings import embed_texts
from app.rag.vector_store import ensure_vector_schema, upsert_document_vectors


def _safe_decode(data: bytes) -> str:
    for encoding in ("utf-8", "latin-1", "ascii"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Unsupported document encoding")


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    cleaned = " ".join(text.split())
    chunks: list[str] = []
    index = 0
    while index < len(cleaned):
        end = min(index + chunk_size, len(cleaned))
        chunks.append(cleaned[index:end])
        index += max(chunk_size - chunk_overlap, 1)
        if len(chunks) > 1000:
            break
    return chunks


def create_document(
    db: Session,
    workspace_id: int,
    owner_id: int,
    filename: str,
    content_type: str,
    size_bytes: int,
    s3_key: str,
) -> Document:
    doc = Document(
        workspace_id=workspace_id,
        owner_id=owner_id,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        s3_key=s3_key,
        status="uploaded",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: int) -> Document | None:
    result = db.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


def list_documents(db: Session, workspace_id: int) -> List[Document]:
    result = db.execute(select(Document).where(Document.workspace_id == workspace_id).order_by(Document.id.desc()))
    return list(result.scalars().all())


def delete_document(db: Session, document_id: int) -> bool:
    doc = get_document(db, document_id)
    if doc is None:
        return False
    db.delete(doc)
    db.commit()
    return True


def list_chunks(db: Session, document_id: int) -> List[DocumentChunk]:
    result = db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index))
    return list(result.scalars().all())


def ingest_document(
    db: Session,
    document_id: int,
    file_bytes: bytes,
    chunk_size: int,
    chunk_overlap: int,
) -> dict[str, Any]:
    doc = get_document(db, document_id)
    if doc is None:
        raise ValueError("Document not found")

    text = _safe_decode(file_bytes)

    existing_count = (
        db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id)).scalars().all()
    )
    if existing_count:
        for chunk in existing_count:
            db.delete(chunk)
        db.commit()

    chunks = _chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    for index, chunk_text in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            content=chunk_text,
            token_count=len(chunk_text.split()),
        )
        db.add(chunk)

    doc.chunk_count = len(chunks)
    db.commit()

    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "document_id": document_id,
        "status": "indexed",
        "records": len(chunks),
        "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, "isoformat") else doc.created_at,
        "completed_at": None,
        "chunks": [{"chunk_index": i, "content": c} for i, c in enumerate(chunks)],
    }
