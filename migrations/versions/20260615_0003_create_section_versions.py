"""create section versions

Revision ID: 20260615_0003
Revises: 20260615_0002
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260615_0003"
down_revision: str | None = "20260615_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "sections_created",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.create_table(
        "section_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("stable_section_key", sa.String(length=1024), nullable=False),
        sa.Column("heading_path", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("heading_level", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("section_checksum", sa.String(length=128), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_version_id",
            "stable_section_key",
            name="uq_section_versions_document_version_id_stable_section_key",
        ),
        sa.UniqueConstraint(
            "document_version_id",
            "ordinal",
            name="uq_section_versions_document_version_id_ordinal",
        ),
    )

    op.create_index(
        "ix_section_versions_document_version_id",
        "section_versions",
        ["document_version_id"],
    )
    op.create_index(
        "ix_section_versions_stable_section_key",
        "section_versions",
        ["stable_section_key"],
    )
    op.create_index(
        "ix_section_versions_section_checksum",
        "section_versions",
        ["section_checksum"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_section_versions_section_checksum",
        table_name="section_versions",
    )
    op.drop_index(
        "ix_section_versions_stable_section_key",
        table_name="section_versions",
    )
    op.drop_index(
        "ix_section_versions_document_version_id",
        table_name="section_versions",
    )
    op.drop_table("section_versions")
    op.drop_column("ingestion_runs", "sections_created")