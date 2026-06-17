"""create llm provider call records

Revision ID: 20260617_0011
Revises: 20260617_0010
Create Date: 2026-06-17 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260617_0011"
down_revision: str | None = "20260617_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_provider_call_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query_trace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column(
            "estimated_cost_usd",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_id"],
            ["answer_records.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["query_trace_id"],
            ["query_traces.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_llm_provider_call_records_answer_id",
        "llm_provider_call_records",
        ["answer_id"],
    )
    op.create_index(
        "ix_llm_provider_call_records_query_trace_id",
        "llm_provider_call_records",
        ["query_trace_id"],
    )
    op.create_index(
        "ix_llm_provider_call_records_status",
        "llm_provider_call_records",
        ["status"],
    )
    op.create_index(
        "ix_llm_provider_call_records_provider_model",
        "llm_provider_call_records",
        ["provider", "model_name"],
    )
    op.create_index(
        "ix_llm_provider_call_records_started_at",
        "llm_provider_call_records",
        ["started_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_llm_provider_call_records_started_at",
        table_name="llm_provider_call_records",
    )
    op.drop_index(
        "ix_llm_provider_call_records_provider_model",
        table_name="llm_provider_call_records",
    )
    op.drop_index(
        "ix_llm_provider_call_records_status",
        table_name="llm_provider_call_records",
    )
    op.drop_index(
        "ix_llm_provider_call_records_query_trace_id",
        table_name="llm_provider_call_records",
    )
    op.drop_index(
        "ix_llm_provider_call_records_answer_id",
        table_name="llm_provider_call_records",
    )
    op.drop_table("llm_provider_call_records")