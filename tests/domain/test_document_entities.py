from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from app.domain.documents.entities import DocumentVersion, IngestionRun, SourceDocument
from app.domain.documents.enums import (
    IngestionRunStatus,
    SourceDocumentStatus,
    SourceSystem,
)


def test_source_document_create_sets_active_status() -> None:
    document = SourceDocument.create(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        external_id="project-atlas-status.md",
        source_uri="seed_documents/project-atlas-status.md",
        title="Project Atlas Status",
    )

    assert document.status == SourceDocumentStatus.ACTIVE
    assert document.current_document_version_id is None
    assert document.deleted_at is None


def test_source_document_can_mark_current_version() -> None:
    document = SourceDocument.create(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        external_id="project-atlas-status.md",
        source_uri="seed_documents/project-atlas-status.md",
        title="Project Atlas Status",
    )
    version_id = uuid4()

    document.mark_current_version(version_id)

    assert document.current_document_version_id == version_id


def test_source_document_requires_deleted_at_when_deleted() -> None:
    with pytest.raises(ValueError, match="deleted_at is required"):
        SourceDocument(
            id=uuid4(),
            source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
            external_id="project-atlas-status.md",
            source_uri="seed_documents/project-atlas-status.md",
            title="Project Atlas Status",
            status=SourceDocumentStatus.DELETED,
        )


def test_document_version_requires_positive_version_number() -> None:
    with pytest.raises(ValueError, match="version_number"):
        DocumentVersion(
            id=uuid4(),
            source_document_id=uuid4(),
            version_number=0,
            content_checksum="content-checksum",
            metadata_checksum="metadata-checksum",
            raw_content="# Project Atlas",
            created_by_run_id=uuid4(),
        )


def test_document_version_is_immutable() -> None:
    version = DocumentVersion(
        id=uuid4(),
        source_document_id=uuid4(),
        version_number=1,
        content_checksum="content-checksum",
        metadata_checksum="metadata-checksum",
        raw_content="# Project Atlas",
        created_by_run_id=uuid4(),
    )

    with pytest.raises(FrozenInstanceError):
        version.version_number = 2  # type: ignore[misc]


def test_ingestion_run_starts_as_running() -> None:
    run = IngestionRun.start(source_system=SourceSystem.LOCAL_SEED_DOCUMENTS)

    assert run.status == IngestionRunStatus.RUNNING
    assert run.completed_at is None


def test_ingestion_run_rejects_changed_count_greater_than_seen_count() -> None:
    run = IngestionRun.start(source_system=SourceSystem.LOCAL_SEED_DOCUMENTS)

    with pytest.raises(ValueError, match="documents_changed cannot exceed documents_seen"):
        run.mark_completed(documents_seen=1, documents_changed=2)