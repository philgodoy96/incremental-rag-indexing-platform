"""create vector index entries

Revision ID: 20260615_0007
Revises: 20260615_0006
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "20260615_0007"
down_revision: str | None = "20260615_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "vector_index_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stable_section_key", sa.String(length=1024), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("embedding_input_hash", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("heading_context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("embedding_vector", Vector(), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_version_id"],
            ["section_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chunk_version_id"],
            ["chunk_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["embedding_record_id"],
            ["embedding_records.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_id",
            "stable_section_key",
            "chunk_index",
            "provider",
            "model_name",
            name="uq_vector_index_entries_logical_identity",
        ),
    )

    op.create_index(
        "ix_vector_index_entries_source_document_id",
        "vector_index_entries",
        ["source_document_id"],
    )
    op.create_index(
        "ix_vector_index_entries_document_version_id",
        "vector_index_entries",
        ["document_version_id"],
    )
    op.create_index(
        "ix_vector_index_entries_section_version_id",
        "vector_index_entries",
        ["section_version_id"],
    )
    op.create_index(
        "ix_vector_index_entries_chunk_version_id",
        "vector_index_entries",
        ["chunk_version_id"],
    )
    op.create_index(
        "ix_vector_index_entries_embedding_record_id",
        "vector_index_entries",
        ["embedding_record_id"],
    )
    op.create_index(
        "ix_vector_index_entries_is_active",
        "vector_index_entries",
        ["is_active"],
    )
    op.create_index(
        "ix_vector_index_entries_provider_model",
        "vector_index_entries",
        ["provider", "model_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_vector_index_entries_provider_model", table_name="vector_index_entries")
    op.drop_index("ix_vector_index_entries_is_active", table_name="vector_index_entries")
    op.drop_index(
        "ix_vector_index_entries_embedding_record_id",
        table_name="vector_index_entries",
    )
    op.drop_index("ix_vector_index_entries_chunk_version_id", table_name="vector_index_entries")
    op.drop_index(
        "ix_vector_index_entries_section_version_id",
        table_name="vector_index_entries",
    )
    op.drop_index(
        "ix_vector_index_entries_document_version_id",
        table_name="vector_index_entries",
    )
    op.drop_index(
        "ix_vector_index_entries_source_document_id",
        table_name="vector_index_entries",
    )
    op.drop_table("vector_index_entries")