from uuid import uuid4

from app.application.services.markdown_section_extraction_service import (
    ExtractedMarkdownSection,
)
from app.application.services.section_delta_planner import (
    SectionDeltaKind,
    SectionDeltaPlanner,
)
from app.domain.documents.entities import SectionVersion


def _section(
    *,
    key: str,
    checksum: str,
    ordinal: int,
    body: str = "body",
) -> SectionVersion:
    return SectionVersion(
        id=uuid4(),
        document_version_id=uuid4(),
        stable_section_key=key,
        heading_path=(key,),
        heading_level=1,
        title=key,
        body=body,
        section_checksum=checksum,
        ordinal=ordinal,
    )


def _extracted(
    *,
    key: str,
    checksum: str,
    ordinal: int,
    body: str = "body",
) -> ExtractedMarkdownSection:
    return ExtractedMarkdownSection(
        stable_section_key=key,
        heading_path=(key,),
        heading_level=1,
        title=key,
        body=body,
        section_checksum=checksum,
        ordinal=ordinal,
    )


def test_section_delta_planner_classifies_unchanged_modified_added_removed() -> None:
    previous = [
        _section(key="summary", checksum="sum-1", ordinal=0),
        _section(key="risks", checksum="risk-1", ordinal=1),
        _section(key="old", checksum="old-1", ordinal=2),
    ]
    incoming = [
        _extracted(key="summary", checksum="sum-1", ordinal=0),
        _extracted(key="risks", checksum="risk-2", ordinal=1),
        _extracted(key="new", checksum="new-1", ordinal=2),
    ]

    plan = SectionDeltaPlanner().plan(
        previous_sections=previous,
        incoming_sections=incoming,
    )

    assert [entry.stable_section_key for entry in plan.unchanged] == ["summary"]
    assert [entry.stable_section_key for entry in plan.modified] == ["risks"]
    assert [entry.stable_section_key for entry in plan.added] == ["new"]
    assert [entry.stable_section_key for entry in plan.removed] == ["old"]
    assert all(entry.kind == SectionDeltaKind.UNCHANGED for entry in plan.unchanged)
    assert all(entry.kind == SectionDeltaKind.MODIFIED for entry in plan.modified)
    assert all(entry.kind == SectionDeltaKind.ADDED for entry in plan.added)
    assert all(entry.kind == SectionDeltaKind.REMOVED for entry in plan.removed)


def test_section_delta_planner_ignores_ordinal_only_reordering() -> None:
    previous = [
        _section(key="summary", checksum="sum-1", ordinal=0),
        _section(key="risks", checksum="risk-1", ordinal=1),
    ]
    incoming = [
        _extracted(key="risks", checksum="risk-1", ordinal=0),
        _extracted(key="summary", checksum="sum-1", ordinal=1),
    ]

    plan = SectionDeltaPlanner().plan(
        previous_sections=previous,
        incoming_sections=incoming,
    )

    assert len(plan.unchanged) == 2
    assert plan.modified == ()
    assert plan.added == ()
    assert plan.removed == ()
