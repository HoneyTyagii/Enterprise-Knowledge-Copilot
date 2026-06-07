import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: int
    workspace_id: int
    filename: str
    content_type: str
    size_bytes: int
    s3_key: str
    status: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    workspace_id: int
    owner_id: int
    filename: str
    content_type: str
    size_bytes: int
    s3_key: str
    status: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkOut(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_count: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class IngestRequest(BaseModel):
    document_id: int = Field(..., gt=0)
    file_bytes: bytes | None = None
    chunk_size: int = Field(default=500, ge=100, le=4000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)


class IngestJobOut(BaseModel):
    id: int
    workspace_id: int
    document_id: int
    status: str
    records: int
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
