"""create retrieval evaluation tables

Revision ID: 20260617_0012
Revises: 20260617_0011
Create Date: 2026-06-17 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260617_0012"
down_revision: str | None = "20260617_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "retrieval_evaluation_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column(
            "expected_chunk_version_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retrieval_evaluation_cases_created_at",
        "retrieval_evaluation_cases",
        ["created_at"],
    )

    op.create_table(
        "retrieval_evaluation_case_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column(
            "expected_chunk_version_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "retrieved_chunk_version_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("hit_count", sa.Integer(), nullable=False),
        sa.Column("recall_at_k", sa.Float(), nullable=False),
        sa.Column("reciprocal_rank", sa.Float(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluation_case_id"],
            ["retrieval_evaluation_cases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_retrieval_evaluation_case_results_evaluation_case_id",
        "retrieval_evaluation_case_results",
        ["evaluation_case_id"],
    )
    op.create_index(
        "ix_retrieval_evaluation_case_results_status",
        "retrieval_evaluation_case_results",
        ["status"],
    )
    op.create_index(
        "ix_retrieval_evaluation_case_results_created_at",
        "retrieval_evaluation_case_results",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_retrieval_evaluation_case_results_created_at",
        table_name="retrieval_evaluation_case_results",
    )
    op.drop_index(
        "ix_retrieval_evaluation_case_results_status",
        table_name="retrieval_evaluation_case_results",
    )
    op.drop_index(
        "ix_retrieval_evaluation_case_results_evaluation_case_id",
        table_name="retrieval_evaluation_case_results",
    )
    op.drop_table("retrieval_evaluation_case_results")

    op.drop_index(
        "ix_retrieval_evaluation_cases_created_at",
        table_name="retrieval_evaluation_cases",
    )
    op.drop_table("retrieval_evaluation_cases")