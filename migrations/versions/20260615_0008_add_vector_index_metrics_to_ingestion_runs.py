"""add vector index metrics to ingestion runs

Revision ID: 20260615_0008
Revises: 20260615_0007
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260615_0008"
down_revision: str | None = "20260615_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "vector_entries_created",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "vector_entries_updated",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "ingestion_runs",
        sa.Column(
            "vector_entries_deactivated",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("ingestion_runs", "vector_entries_deactivated")
    op.drop_column("ingestion_runs", "vector_entries_updated")
    op.drop_column("ingestion_runs", "vector_entries_created")