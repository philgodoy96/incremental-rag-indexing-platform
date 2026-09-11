from dataclasses import dataclass
from enum import StrEnum

from app.application.services.markdown_section_extraction_service import (
    ExtractedMarkdownSection,
)
from app.domain.documents.entities import SectionVersion


class SectionDeltaKind(StrEnum):
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    ADDED = "added"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class SectionDeltaEntry:
    kind: SectionDeltaKind
    stable_section_key: str
    previous: SectionVersion | None = None
    incoming: ExtractedMarkdownSection | None = None


@dataclass(frozen=True, slots=True)
class SectionDeltaPlan:
    unchanged: tuple[SectionDeltaEntry, ...]
    modified: tuple[SectionDeltaEntry, ...]
    added: tuple[SectionDeltaEntry, ...]
    removed: tuple[SectionDeltaEntry, ...]

    @property
    def entries(self) -> tuple[SectionDeltaEntry, ...]:
        return (*self.unchanged, *self.modified, *self.added, *self.removed)


class SectionDeltaPlanner:
    """Deterministically classifies section changes between two document snapshots."""

    def plan(
        self,
        *,
        previous_sections: list[SectionVersion],
        incoming_sections: list[ExtractedMarkdownSection],
    ) -> SectionDeltaPlan:
        previous_by_key = {
            section.stable_section_key: section for section in previous_sections
        }
        incoming_keys: set[str] = set()

        unchanged: list[SectionDeltaEntry] = []
        modified: list[SectionDeltaEntry] = []
        added: list[SectionDeltaEntry] = []

        for incoming in incoming_sections:
            incoming_keys.add(incoming.stable_section_key)
            previous = previous_by_key.get(incoming.stable_section_key)

            if previous is None:
                added.append(
                    SectionDeltaEntry(
                        kind=SectionDeltaKind.ADDED,
                        stable_section_key=incoming.stable_section_key,
                        incoming=incoming,
                    )
                )
                continue

            if previous.section_checksum == incoming.section_checksum:
                unchanged.append(
                    SectionDeltaEntry(
                        kind=SectionDeltaKind.UNCHANGED,
                        stable_section_key=incoming.stable_section_key,
                        previous=previous,
                        incoming=incoming,
                    )
                )
                continue

            modified.append(
                SectionDeltaEntry(
                    kind=SectionDeltaKind.MODIFIED,
                    stable_section_key=incoming.stable_section_key,
                    previous=previous,
                    incoming=incoming,
                )
            )

        removed = [
            SectionDeltaEntry(
                kind=SectionDeltaKind.REMOVED,
                stable_section_key=previous.stable_section_key,
                previous=previous,
            )
            for previous in previous_sections
            if previous.stable_section_key not in incoming_keys
        ]

        return SectionDeltaPlan(
            unchanged=tuple(unchanged),
            modified=tuple(modified),
            added=tuple(added),
            removed=tuple(removed),
        )
