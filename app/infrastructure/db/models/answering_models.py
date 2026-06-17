from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class AnswerRecordModel(Base):
    __tablename__ = "answer_records"

    __table_args__ = (
        Index("ix_answer_records_query_trace_id", "query_trace_id"),
        Index("ix_answer_records_status", "status"),
        Index("ix_answer_records_created_at", "created_at"),
        Index("ix_answer_records_provider_model", "provider", "model_name"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    query_trace_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("query_traces.id", ondelete="RESTRICT"),
        nullable=False,
    )
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnswerCitationRecordModel(Base):
    __tablename__ = "answer_citation_records"

    __table_args__ = (
        Index("ix_answer_citation_records_answer_id", "answer_id"),
        Index("ix_answer_citation_records_rank", "answer_id", "rank"),
        Index(
            "ix_answer_citation_records_vector_index_entry_id",
            "vector_index_entry_id",
        ),
        Index("ix_answer_citation_records_source_document_id", "source_document_id"),
        Index("ix_answer_citation_records_document_version_id", "document_version_id"),
        Index("ix_answer_citation_records_chunk_version_id", "chunk_version_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    answer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("answer_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_index_entry_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    source_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    document_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    section_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    chunk_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    embedding_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    stable_section_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading_context: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    distance: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)