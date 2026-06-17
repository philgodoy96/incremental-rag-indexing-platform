from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class RetrievalEvaluationCaseModel(Base):
    __tablename__ = "retrieval_evaluation_cases"

    __table_args__ = (
        Index("ix_retrieval_evaluation_cases_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    expected_chunk_version_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RetrievalEvaluationCaseResultModel(Base):
    __tablename__ = "retrieval_evaluation_case_results"

    __table_args__ = (
        Index(
            "ix_retrieval_evaluation_case_results_evaluation_case_id",
            "evaluation_case_id",
        ),
        Index("ix_retrieval_evaluation_case_results_status", "status"),
        Index("ix_retrieval_evaluation_case_results_created_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    evaluation_case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("retrieval_evaluation_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    expected_chunk_version_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
    )
    retrieved_chunk_version_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recall_at_k: Mapped[float] = mapped_column(Float, nullable=False)
    reciprocal_rank: Mapped[float] = mapped_column(Float, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)