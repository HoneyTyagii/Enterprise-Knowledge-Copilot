import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, Workspace
from app.db.session import get_db
from app.ingestion.schemas import (
    ChunkOut,
    DocumentOut,
    DocumentUploadResponse,
    IngestJobOut,
)
from app.ingestion.service import (
    create_document,
    delete_document,
    get_document,
    ingest_document,
    list_chunks,
    list_documents,
)
from app.multitenancy.dependencies import require_tenant_context
from app.multitenancy.context import TenantContext
from app.rbac.dependencies import require_permission
from app.storage.s3 import s3_storage

router = APIRouter(prefix="/api/v1/workspaces", tags=["ingestion"])


@router.post(
    "/{workspace_id}/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(require_permission("ingest", "document")),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    workspace = db.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
    if workspace is None or workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found or access denied")

    contents = await file.read()
    doc = create_document(
        db,
        workspace_id=workspace_id,
        owner_id=ctx.actor_user_id,
        filename=file.filename or "uploaded_file",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        s3_key="",
    )

    storage_key = f"workspaces/{workspace_id}/documents/{doc.id}/{file.filename}"
    s3_storage.upload(storage_key, contents, file.content_type or "application/octet-stream")

    doc.s3_key = storage_key
    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse.model_validate(doc)


@router.get("/{workspace_id}/documents", response_model=List[DocumentOut])
async def list_documents_endpoint(
    workspace_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> List[DocumentOut]:
    workspace = db.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
    if workspace is None or workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found or access denied")

    documents = list_documents(db, workspace_id=workspace_id)
    return [DocumentOut.model_validate(d) for d in documents]


@router.get("/{workspace_id}/documents/{document_id}", response_model=DocumentOut)
async def get_document_endpoint(
    workspace_id: int,
    document_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> DocumentOut:
    document = get_document(db, document_id)
    if document is None or document.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    workspace = db.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
    if workspace is None or workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found or access denied")

    return DocumentOut.model_validate(document)


@router.delete(
    "/{workspace_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document_endpoint(
    workspace_id: int,
    document_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    document = get_document(db, document_id)
    if document is None or document.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    workspace = db.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
    if workspace is None or workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found or access denied")

    s3_storage.delete(document.s3_key)
    delete_document(db, document_id)


@router.post(
    "/{workspace_id}/documents/ingest",
    response_model=IngestJobOut,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_document_endpoint(
    workspace_id: int,
    document_id: int = Form(...),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    ctx: TenantContext = Depends(require_permission("ingest", "document")),
    db: Session = Depends(get_db),
) -> IngestJobOut:
    workspace = db.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
    if workspace is None or workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found or access denied")

    document = get_document(db, document_id)
    if document is None or document.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in this workspace")

    if not document.s3_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has no stored file to ingest")

    stored_bytes = s3_storage.get_object(document.s3_key)
    job = ingest_document(
        db,
        document_id=document_id,
        file_bytes=stored_bytes,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    document.status = "indexed"
    document.chunk_count = len(job["chunks"])
    db.commit()

    return IngestJobOut.model_validate(job)


@router.get("/{workspace_id}/documents/{document_id}/chunks", response_model=List[ChunkOut])
async def list_chunks_endpoint(
    workspace_id: int,
    document_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> List[ChunkOut]:
    document = get_document(db, document_id)
    if document is None or document.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    workspace = db.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
    if workspace is None or workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found or access denied")

    chunks = list_chunks(db, document_id=document_id)
    return [ChunkOut.model_validate(c) for c in chunks]

