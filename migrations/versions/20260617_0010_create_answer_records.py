"""create answer records

Revision ID: 20260617_0010
Revises: 20260615_0009
Create Date: 2026-06-17 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260617_0010"
down_revision: str | None = "20260615_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "answer_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("query_trace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["query_trace_id"],
            ["query_traces.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_answer_records_query_trace_id",
        "answer_records",
        ["query_trace_id"],
    )
    op.create_index("ix_answer_records_status", "answer_records", ["status"])
    op.create_index("ix_answer_records_created_at", "answer_records", ["created_at"])
    op.create_index(
        "ix_answer_records_provider_model",
        "answer_records",
        ["provider", "model_name"],
    )

    op.create_table(
        "answer_citation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("vector_index_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stable_section_key", sa.String(length=1024), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("heading_context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_id"],
            ["answer_records.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_answer_citation_records_answer_id",
        "answer_citation_records",
        ["answer_id"],
    )
    op.create_index(
        "ix_answer_citation_records_rank",
        "answer_citation_records",
        ["answer_id", "rank"],
    )
    op.create_index(
        "ix_answer_citation_records_vector_index_entry_id",
        "answer_citation_records",
        ["vector_index_entry_id"],
    )
    op.create_index(
        "ix_answer_citation_records_source_document_id",
        "answer_citation_records",
        ["source_document_id"],
    )
    op.create_index(
        "ix_answer_citation_records_document_version_id",
        "answer_citation_records",
        ["document_version_id"],
    )
    op.create_index(
        "ix_answer_citation_records_chunk_version_id",
        "answer_citation_records",
        ["chunk_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_answer_citation_records_chunk_version_id",
        table_name="answer_citation_records",
    )
    op.drop_index(
        "ix_answer_citation_records_document_version_id",
        table_name="answer_citation_records",
    )
    op.drop_index(
        "ix_answer_citation_records_source_document_id",
        table_name="answer_citation_records",
    )
    op.drop_index(
        "ix_answer_citation_records_vector_index_entry_id",
        table_name="answer_citation_records",
    )
    op.drop_index(
        "ix_answer_citation_records_rank",
        table_name="answer_citation_records",
    )
    op.drop_index(
        "ix_answer_citation_records_answer_id",
        table_name="answer_citation_records",
    )
    op.drop_table("answer_citation_records")

    op.drop_index("ix_answer_records_provider_model", table_name="answer_records")
    op.drop_index("ix_answer_records_created_at", table_name="answer_records")
    op.drop_index("ix_answer_records_status", table_name="answer_records")
    op.drop_index("ix_answer_records_query_trace_id", table_name="answer_records")
    op.drop_table("answer_records")