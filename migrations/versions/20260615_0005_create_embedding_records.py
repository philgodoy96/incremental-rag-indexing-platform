"""create embedding records

Revision ID: 20260615_0005
Revises: 20260615_0004
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260615_0005"
down_revision: str | None = "20260615_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "embeddings_created",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "embedding_tokens_processed",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "estimated_embedding_cost_usd_micros",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.create_table(
        "embedding_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("embedding_input_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "embedding_vector",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("input_token_estimate", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["chunk_version_id"],
            ["chunk_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chunk_version_id",
            "provider",
            "model_name",
            "embedding_input_hash",
            name="uq_embedding_records_identity",
        ),
    )

    op.create_index(
        "ix_embedding_records_chunk_version_id",
        "embedding_records",
        ["chunk_version_id"],
    )
    op.create_index(
        "ix_embedding_records_embedding_input_hash",
        "embedding_records",
        ["embedding_input_hash"],
    )
    op.create_index(
        "ix_embedding_records_provider_model",
        "embedding_records",
        ["provider", "model_name"],
    )

    op.create_table(
        "embedding_cost_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("input_token_estimate", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd_micros", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"],
            ["ingestion_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["embedding_record_id"],
            ["embedding_records.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_embedding_cost_records_ingestion_run_id",
        "embedding_cost_records",
        ["ingestion_run_id"],
    )
    op.create_index(
        "ix_embedding_cost_records_embedding_record_id",
        "embedding_cost_records",
        ["embedding_record_id"],
    )
    op.create_index(
        "ix_embedding_cost_records_provider_model",
        "embedding_cost_records",
        ["provider", "model_name"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_embedding_cost_records_provider_model",
        table_name="embedding_cost_records",
    )
    op.drop_index(
        "ix_embedding_cost_records_embedding_record_id",
        table_name="embedding_cost_records",
    )
    op.drop_index(
        "ix_embedding_cost_records_ingestion_run_id",
        table_name="embedding_cost_records",
    )
    op.drop_table("embedding_cost_records")

    op.drop_index(
        "ix_embedding_records_provider_model",
        table_name="embedding_records",
    )
    op.drop_index(
        "ix_embedding_records_embedding_input_hash",
        table_name="embedding_records",
    )
    op.drop_index(
        "ix_embedding_records_chunk_version_id",
        table_name="embedding_records",
    )
    op.drop_table("embedding_records")

    op.drop_column("ingestion_runs", "estimated_embedding_cost_usd_micros")
    op.drop_column("ingestion_runs", "embedding_tokens_processed")
    op.drop_column("ingestion_runs", "embeddings_created")