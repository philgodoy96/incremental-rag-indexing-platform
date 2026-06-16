from uuid import uuid4

from app.application.services.markdown_section_extraction_service import (
    MarkdownSectionExtractionService,
    build_stable_section_key,
    slugify_heading,
)


def test_extracts_sections_from_markdown_headings() -> None:
    content = """# Project Atlas Status

## Summary

Project Atlas is at risk.

## Risks

Evaluation dataset is delayed.
"""

    service = MarkdownSectionExtractionService()

    sections = service.extract(content=content, fallback_title="Project Atlas Status")

    assert len(sections) == 2
    assert sections[0].title == "Summary"
    assert sections[0].heading_path == ("Project Atlas Status", "Summary")
    assert sections[0].stable_section_key == "project-atlas-status/summary"
    assert sections[0].ordinal == 0
    assert sections[1].title == "Risks"
    assert sections[1].ordinal == 1


def test_extracts_nested_heading_path() -> None:
    content = """# Redis Queue Backlog Runbook

## Mitigation Steps

### Worker Saturation

Scale workers horizontally.
"""

    service = MarkdownSectionExtractionService()

    sections = service.extract(
        content=content,
        fallback_title="Redis Queue Backlog Runbook",
    )

    assert len(sections) == 1
    assert sections[0].heading_path == (
        "Redis Queue Backlog Runbook",
        "Mitigation Steps",
        "Worker Saturation",
    )
    assert (
        sections[0].stable_section_key
        == "redis-queue-backlog-runbook/mitigation-steps/worker-saturation"
    )


def test_duplicate_heading_paths_receive_deterministic_suffixes() -> None:
    content = """# Runbook

## Notes

First note.

## Notes

Second note.
"""

    service = MarkdownSectionExtractionService()

    sections = service.extract(content=content, fallback_title="Runbook")

    assert sections[0].stable_section_key == "runbook/notes"
    assert sections[1].stable_section_key == "runbook/notes--2"


def test_ignores_empty_sections() -> None:
    content = """# Project Atlas

## Empty

## Summary

Status: At Risk.
"""

    service = MarkdownSectionExtractionService()

    sections = service.extract(content=content, fallback_title="Project Atlas")

    assert len(sections) == 1
    assert sections[0].title == "Summary"


def test_extracts_document_without_headings_using_fallback_title() -> None:
    content = "Standalone operational note."

    service = MarkdownSectionExtractionService()

    sections = service.extract(content=content, fallback_title="Operational Note")

    assert len(sections) == 1
    assert sections[0].heading_path == ("Operational Note",)
    assert sections[0].stable_section_key == "operational-note"


def test_create_section_versions_assigns_document_version_id() -> None:
    document_version_id = uuid4()
    content = """# Project Atlas

## Summary

Status: At Risk.
"""

    service = MarkdownSectionExtractionService()

    section_versions = service.create_section_versions(
        document_version_id=document_version_id,
        content=content,
        fallback_title="Project Atlas",
    )

    assert len(section_versions) == 1
    assert section_versions[0].document_version_id == document_version_id


def test_slugify_heading_normalizes_heading_text() -> None:
    assert slugify_heading("Retry Safety!") == "retry-safety"


def test_build_stable_section_key_uses_heading_path() -> None:
    assert (
        build_stable_section_key(("Redis Runbook", "Initial Triage"))
        == "redis-runbook/initial-triage"
    )