"""create document foundation tables

Revision ID: 20260615_0002
Revises: 20260615_0001
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260615_0002"
down_revision: str | None = "20260615_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "documents_seen",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "documents_changed",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "current_document_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_system",
            "external_id",
            name="uq_source_documents_source_system_external_id",
        ),
    )

    op.create_index(
        "ix_source_documents_source_system",
        "source_documents",
        ["source_system"],
    )
    op.create_index(
        "ix_source_documents_status",
        "source_documents",
        ["status"],
    )

    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_document_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content_checksum", sa.String(length=128), nullable=False),
        sa.Column("metadata_checksum", sa.String(length=128), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column(
            "created_by_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_run_id"],
            ["ingestion_runs.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["source_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_document_id",
            "version_number",
            name="uq_document_versions_source_document_id_version_number",
        ),
    )

    op.create_index(
        "ix_document_versions_source_document_id",
        "document_versions",
        ["source_document_id"],
    )
    op.create_index(
        "ix_document_versions_content_checksum",
        "document_versions",
        ["content_checksum"],
    )

    op.create_foreign_key(
        "fk_source_documents_current_document_version_id",
        "source_documents",
        "document_versions",
        ["current_document_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_source_documents_current_document_version_id",
        "source_documents",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_document_versions_content_checksum",
        table_name="document_versions",
    )
    op.drop_index(
        "ix_document_versions_source_document_id",
        table_name="document_versions",
    )
    op.drop_table("document_versions")

    op.drop_index("ix_source_documents_status", table_name="source_documents")
    op.drop_index(
        "ix_source_documents_source_system",
        table_name="source_documents",
    )
    op.drop_table("source_documents")
    op.drop_table("ingestion_runs")