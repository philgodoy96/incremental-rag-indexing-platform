from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class IngestionRunModel(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    documents_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    documents_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)


class SourceDocumentModel(Base):
    __tablename__ = "source_documents"

    __table_args__ = (
        UniqueConstraint(
            "source_system",
            "external_id",
            name="uq_source_documents_source_system_external_id",
        ),
        Index("ix_source_documents_source_system", "source_system"),
        Index("ix_source_documents_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    source_uri: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_document_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "document_versions.id",
            name="fk_source_documents_current_document_version_id",
            ondelete="SET NULL",
            use_alter=True,
        ),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentVersionModel(Base):
    __tablename__ = "document_versions"

    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "version_number",
            name="uq_document_versions_source_document_id_version_number",
        ),
        Index("ix_document_versions_source_document_id", "source_document_id"),
        Index("ix_document_versions_content_checksum", "content_checksum"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    source_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ingestion_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)