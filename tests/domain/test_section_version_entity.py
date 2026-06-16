from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from app.domain.documents.entities import SectionVersion


def test_section_version_requires_valid_heading_level() -> None:
    with pytest.raises(ValueError, match="heading_level"):
        SectionVersion(
            id=uuid4(),
            document_version_id=uuid4(),
            stable_section_key="project-atlas/summary",
            heading_path=("Project Atlas", "Summary"),
            heading_level=7,
            title="Summary",
            body="Status: At Risk",
            section_checksum="checksum",
            ordinal=0,
        )


def test_section_version_requires_non_empty_heading_path() -> None:
    with pytest.raises(ValueError, match="heading_path"):
        SectionVersion(
            id=uuid4(),
            document_version_id=uuid4(),
            stable_section_key="summary",
            heading_path=(),
            heading_level=2,
            title="Summary",
            body="Status: At Risk",
            section_checksum="checksum",
            ordinal=0,
        )


def test_section_version_is_immutable() -> None:
    section = SectionVersion(
        id=uuid4(),
        document_version_id=uuid4(),
        stable_section_key="project-atlas/summary",
        heading_path=("Project Atlas", "Summary"),
        heading_level=2,
        title="Summary",
        body="Status: At Risk",
        section_checksum="checksum",
        ordinal=0,
    )

    with pytest.raises(FrozenInstanceError):
        section.title = "Changed"  # type: ignore[misc]