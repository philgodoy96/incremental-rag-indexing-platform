from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
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
    sections_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embeddings_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embeddings_reused: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_tokens_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    estimated_embedding_cost_usd_micros: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
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


class SectionVersionModel(Base):
    __tablename__ = "section_versions"

    __table_args__ = (
        UniqueConstraint(
            "document_version_id",
            "stable_section_key",
            name="uq_section_versions_document_version_id_stable_section_key",
        ),
        UniqueConstraint(
            "document_version_id",
            "ordinal",
            name="uq_section_versions_document_version_id_ordinal",
        ),
        Index("ix_section_versions_document_version_id", "document_version_id"),
        Index("ix_section_versions_stable_section_key", "stable_section_key"),
        Index("ix_section_versions_section_checksum", "section_checksum"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    document_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    stable_section_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    heading_path: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    heading_level: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    section_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChunkVersionModel(Base):
    __tablename__ = "chunk_versions"

    __table_args__ = (
        UniqueConstraint(
            "section_version_id",
            "chunk_index",
            name="uq_chunk_versions_section_version_id_chunk_index",
        ),
        Index("ix_chunk_versions_section_version_id", "section_version_id"),
        Index("ix_chunk_versions_chunk_hash", "chunk_hash"),
        Index("ix_chunk_versions_embedding_input_hash", "embedding_input_hash"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    section_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("section_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    heading_context: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_flags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EmbeddingRecordModel(Base):
    __tablename__ = "embedding_records"

    __table_args__ = (
        UniqueConstraint(
            "chunk_version_id",
            "provider",
            "model_name",
            "embedding_input_hash",
            name="uq_embedding_records_identity",
        ),
        Index("ix_embedding_records_chunk_version_id", "chunk_version_id"),
        Index("ix_embedding_records_embedding_input_hash", "embedding_input_hash"),
        Index("ix_embedding_records_provider_model", "provider", "model_name"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    chunk_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chunk_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_vector: Mapped[list[float]] = mapped_column(JSONB, nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    input_token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChunkEmbeddingLinkModel(Base):
    __tablename__ = "chunk_embedding_links"

    __table_args__ = (
        UniqueConstraint(
            "chunk_version_id",
            name="uq_chunk_embedding_links_chunk_version_id",
        ),
        Index("ix_chunk_embedding_links_embedding_record_id", "embedding_record_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    chunk_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chunk_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("embedding_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class VectorIndexEntryModel(Base):
    __tablename__ = "vector_index_entries"

    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "stable_section_key",
            "chunk_index",
            "provider",
            "model_name",
            name="uq_vector_index_entries_logical_identity",
        ),
        Index("ix_vector_index_entries_source_document_id", "source_document_id"),
        Index("ix_vector_index_entries_document_version_id", "document_version_id"),
        Index("ix_vector_index_entries_section_version_id", "section_version_id"),
        Index("ix_vector_index_entries_chunk_version_id", "chunk_version_id"),
        Index("ix_vector_index_entries_embedding_record_id", "embedding_record_id"),
        Index("ix_vector_index_entries_is_active", "is_active"),
        Index("ix_vector_index_entries_provider_model", "provider", "model_name"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    source_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("section_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chunk_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("embedding_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    stable_section_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    heading_context: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    embedding_vector: Mapped[list[float]] = mapped_column(Vector(), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EmbeddingCostRecordModel(Base):
    __tablename__ = "embedding_cost_records"

    __table_args__ = (
        Index("ix_embedding_cost_records_ingestion_run_id", "ingestion_run_id"),
        Index("ix_embedding_cost_records_embedding_record_id", "embedding_record_id"),
        Index("ix_embedding_cost_records_provider_model", "provider", "model_name"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ingestion_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("embedding_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_token_estimate: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)