from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    content_fingerprint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_version"),
    )


class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    version_id: Mapped[int] = mapped_column(ForeignKey("document_versions.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


def is_probably_same_content_fingerprint(previous: Optional[str], current: Optional[str]) -> bool:
    return previous is not None and current is not None and previous == current

