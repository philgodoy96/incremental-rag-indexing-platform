import pytest

from app.domain.documents.enums import SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate


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