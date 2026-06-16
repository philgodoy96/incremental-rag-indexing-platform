"""create chunk embedding links

Revision ID: 20260615_0006
Revises: 20260615_0005
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260615_0006"
down_revision: str | None = "20260615_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "embeddings_reused",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.create_table(
        "chunk_embedding_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
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
            "chunk_version_id",
            name="uq_chunk_embedding_links_chunk_version_id",
        ),
    )

    op.create_index(
        "ix_chunk_embedding_links_embedding_record_id",
        "chunk_embedding_links",
        ["embedding_record_id"],
    )

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.execute(
        """
        INSERT INTO chunk_embedding_links (
            id,
            chunk_version_id,
            embedding_record_id,
            created_at
        )
        SELECT
            gen_random_uuid(),
            chunk_version_id,
            id,
            created_at
        FROM embedding_records
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chunk_embedding_links_embedding_record_id",
        table_name="chunk_embedding_links",
    )
    op.drop_table("chunk_embedding_links")
    op.drop_column("ingestion_runs", "embeddings_reused")