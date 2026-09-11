"""separate section snapshot membership from section content

Revision ID: 20260618_0013
Revises: 20260617_0012
Create Date: 2026-06-18 00:00:00.000000

Downgrade policy
----------------
This migration is intentionally irreversible.

After upgrade, a single ``section_versions`` content row may be referenced by
multiple ``document_version_sections`` memberships. The previous schema required
exactly one ``SectionVersion`` row per ``DocumentVersion``.

A data-preserving downgrade would need to rematerialize shared section/chunk
artifacts per historical membership and remap dependent identities across:

- ``chunk_versions``
- ``chunk_embedding_links`` / ``embedding_records`` provenance
- ``vector_index_entries`` foreign keys
- denormalized audit identifiers in answer citations and query-trace hits
- evaluation case JSONB chunk-id lists

That reconstruction is disproportionate and unsafe to perform silently in this
migration without a dedicated rematerialization procedure and integration
harness. A lossy ``UPDATE ... FROM document_version_sections`` would discard
historical snapshot membership and is therefore forbidden.

Operational rollback: restore from backup taken before upgrade, or apply a
dedicated roll-forward migration. Do not use ``alembic downgrade`` for this
revision.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260618_0013"
down_revision: str | None = "20260617_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

IRREVERSIBLE_DOWNGRADE_MESSAGE = (
    "Migration 20260618_0013 is irreversible: SectionVersion content may be shared "
    "across DocumentVersion snapshots via document_version_sections. Downgrading "
    "cannot safely reconstruct the previous one-SectionVersion-per-DocumentVersion "
    "representation without a dedicated rematerialization of shared sections, "
    "chunks, embedding links, vector projection FKs, and denormalized audit "
    "identifiers. A lossy downgrade would discard historical snapshot membership "
    "and is not permitted. Roll back via backup/restore taken before upgrade, or "
    "apply a dedicated roll-forward migration."
)


def upgrade() -> None:
    op.create_table(
        "document_version_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "section_version_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_version_id"],
            ["section_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_version_id",
            "section_version_id",
            name="uq_document_version_sections_document_version_id_section_version_id",
        ),
        sa.UniqueConstraint(
            "document_version_id",
            "ordinal",
            name="uq_document_version_sections_document_version_id_ordinal",
        ),
    )
    op.create_index(
        "ix_document_version_sections_document_version_id",
        "document_version_sections",
        ["document_version_id"],
    )
    op.create_index(
        "ix_document_version_sections_section_version_id",
        "document_version_sections",
        ["section_version_id"],
    )

    op.execute(
        """
        INSERT INTO document_version_sections (
            id,
            document_version_id,
            section_version_id,
            ordinal,
            created_at
        )
        SELECT
            gen_random_uuid(),
            document_version_id,
            id,
            ordinal,
            created_at
        FROM section_versions
        """
    )

    op.drop_constraint(
        "uq_section_versions_document_version_id_stable_section_key",
        "section_versions",
        type_="unique",
    )
    op.drop_constraint(
        "uq_section_versions_document_version_id_ordinal",
        "section_versions",
        type_="unique",
    )
    op.drop_index(
        "ix_section_versions_document_version_id",
        table_name="section_versions",
    )
    op.drop_constraint(
        "section_versions_document_version_id_fkey",
        "section_versions",
        type_="foreignkey",
    )
    op.drop_column("section_versions", "document_version_id")
    op.drop_column("section_versions", "ordinal")


def downgrade() -> None:
    """Refuse downgrade before any schema or data mutation.

    Shared section content cannot be collapsed back into the previous
    one-row-per-DocumentVersion model without a dedicated rematerialization
    procedure. Failing loudly preserves the post-upgrade schema/data state.
    """

    raise RuntimeError(IRREVERSIBLE_DOWNGRADE_MESSAGE)
