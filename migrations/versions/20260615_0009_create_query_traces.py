"""create query traces

Revision ID: 20260615_0009
Revises: 20260615_0008
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260615_0009"
down_revision: str | None = "20260615_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "query_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("query_embedding_dimensions", sa.Integer(), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_query_traces_status", "query_traces", ["status"])
    op.create_index("ix_query_traces_started_at", "query_traces", ["started_at"])
    op.create_index(
        "ix_query_traces_provider_model",
        "query_traces",
        ["provider", "model_name"],
    )

    op.create_table(
        "query_trace_hits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query_trace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("vector_index_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stable_section_key", sa.String(length=1024), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("heading_context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["query_trace_id"],
            ["query_traces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_query_trace_hits_query_trace_id",
        "query_trace_hits",
        ["query_trace_id"],
    )
    op.create_index(
        "ix_query_trace_hits_rank",
        "query_trace_hits",
        ["query_trace_id", "rank"],
    )
    op.create_index(
        "ix_query_trace_hits_vector_index_entry_id",
        "query_trace_hits",
        ["vector_index_entry_id"],
    )
    op.create_index(
        "ix_query_trace_hits_source_document_id",
        "query_trace_hits",
        ["source_document_id"],
    )
    op.create_index(
        "ix_query_trace_hits_document_version_id",
        "query_trace_hits",
        ["document_version_id"],
    )
    op.create_index(
        "ix_query_trace_hits_chunk_version_id",
        "query_trace_hits",
        ["chunk_version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_query_trace_hits_chunk_version_id", table_name="query_trace_hits")
    op.drop_index("ix_query_trace_hits_document_version_id", table_name="query_trace_hits")
    op.drop_index("ix_query_trace_hits_source_document_id", table_name="query_trace_hits")
    op.drop_index(
        "ix_query_trace_hits_vector_index_entry_id",
        table_name="query_trace_hits",
    )
    op.drop_index("ix_query_trace_hits_rank", table_name="query_trace_hits")
    op.drop_index("ix_query_trace_hits_query_trace_id", table_name="query_trace_hits")
    op.drop_table("query_trace_hits")

    op.drop_index("ix_query_traces_provider_model", table_name="query_traces")
    op.drop_index("ix_query_traces_started_at", table_name="query_traces")
    op.drop_index("ix_query_traces_status", table_name="query_traces")
    op.drop_table("query_traces")