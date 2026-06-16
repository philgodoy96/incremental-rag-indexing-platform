"""create chunk versions

Revision ID: 20260615_0004
Revises: 20260615_0003
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260615_0004"
down_revision: str | None = "20260615_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "chunks_created",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.create_table(
        "chunk_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "section_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("heading_context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("chunk_hash", sa.String(length=128), nullable=False),
        sa.Column("embedding_input_hash", sa.String(length=128), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column(
            "risk_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["section_version_id"],
            ["section_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "section_version_id",
            "chunk_index",
            name="uq_chunk_versions_section_version_id_chunk_index",
        ),
    )

    op.create_index(
        "ix_chunk_versions_section_version_id",
        "chunk_versions",
        ["section_version_id"],
    )
    op.create_index(
        "ix_chunk_versions_chunk_hash",
        "chunk_versions",
        ["chunk_hash"],
    )
    op.create_index(
        "ix_chunk_versions_embedding_input_hash",
        "chunk_versions",
        ["embedding_input_hash"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chunk_versions_embedding_input_hash",
        table_name="chunk_versions",
    )
    op.drop_index("ix_chunk_versions_chunk_hash", table_name="chunk_versions")
    op.drop_index(
        "ix_chunk_versions_section_version_id",
        table_name="chunk_versions",
    )
    op.drop_table("chunk_versions")
    op.drop_column("ingestion_runs", "chunks_created")