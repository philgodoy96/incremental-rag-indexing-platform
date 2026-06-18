import pytest

from app.domain.documents.enums import SourceSystem
from app.domain.documents.source_candidates import (
    SourceDocumentCandidate,
    normalize_source_uri,
)


def test_source_document_candidate_normalizes_external_id_and_source_uri() -> None:
    candidate = SourceDocumentCandidate.create(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        external_id="runbooks\\redis-queue-backlog-runbook.md",
        source_uri="seed_documents\\runbooks\\redis-queue-backlog-runbook.md",
        title="Redis Queue Backlog Runbook",
        raw_content="# Redis Queue Backlog Runbook\n\nInitial triage steps.",
    )

    assert candidate.external_id == "runbooks/redis-queue-backlog-runbook.md"
    assert candidate.source_uri == "seed_documents/runbooks/redis-queue-backlog-runbook.md"


def test_source_document_candidate_rejects_blank_raw_content() -> None:
    with pytest.raises(ValueError, match="raw_content must not be blank"):
        SourceDocumentCandidate.create(
            source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
            external_id="empty.md",
            source_uri="seed_documents/empty.md",
            title="Empty",
            raw_content="",
        )


def test_source_document_candidate_calculates_checksums() -> None:
    candidate = SourceDocumentCandidate.create(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        external_id="project-atlas-status.md",
        source_uri="seed_documents/project-atlas-status.md",
        title="Project Atlas Status",
        raw_content="# Project Atlas Status\n\nStatus: On Track.",
    )

    assert candidate.content_checksum
    assert candidate.metadata_checksum
    assert candidate.content_checksum != candidate.metadata_checksum


def test_normalize_source_uri_preserves_scheme_based_uris() -> None:
    assert normalize_source_uri("demo://project-atlas-brief") == "demo://project-atlas-brief"


def test_source_document_candidate_preserves_tags_in_metadata_checksum() -> None:
    without_tags = SourceDocumentCandidate.create(
        source_system=SourceSystem.DEMO_DOCUMENTS,
        external_id="demo/project-atlas-brief",
        source_uri="demo://project-atlas-brief",
        title="Project Atlas Brief",
        raw_content="# Project Atlas Brief\n\nContent.",
    )
    with_tags = SourceDocumentCandidate.create(
        source_system=SourceSystem.DEMO_DOCUMENTS,
        external_id="demo/project-atlas-brief",
        source_uri="demo://project-atlas-brief",
        title="Project Atlas Brief",
        raw_content="# Project Atlas Brief\n\nContent.",
        tags=("project-atlas", "platform"),
    )

    assert with_tags.tags == ("project-atlas", "platform")
    assert with_tags.metadata_checksum != without_tags.metadata_checksum