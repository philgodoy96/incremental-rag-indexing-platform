import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.domain.documents.checksums import calculate_content_checksum
from app.domain.documents.entities import SectionVersion

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class ExtractedMarkdownSection:
    stable_section_key: str
    heading_path: tuple[str, ...]
    heading_level: int
    title: str
    body: str
    section_checksum: str
    ordinal: int


class MarkdownSectionExtractionService:
    """Extracts deterministic sections from Markdown content."""

    def extract(self, *, content: str, fallback_title: str) -> list[ExtractedMarkdownSection]:
        lines = content.splitlines()
        heading_stack: list[tuple[int, str]] = []

        current_level: int | None = None
        current_title: str | None = None
        current_heading_path: tuple[str, ...] = ()
        current_body_lines: list[str] = []

        extracted_sections: list[ExtractedMarkdownSection] = []
        key_counts: dict[str, int] = {}

        def flush_current_section() -> None:
            nonlocal current_body_lines

            if current_level is None or current_title is None:
                return

            body = "\n".join(current_body_lines).strip()

            if not body:
                current_body_lines = []
                return

            base_key = build_stable_section_key(current_heading_path)
            occurrence = key_counts.get(base_key, 0) + 1
            key_counts[base_key] = occurrence

            stable_key = base_key if occurrence == 1 else f"{base_key}--{occurrence}"

            extracted_sections.append(
                ExtractedMarkdownSection(
                    stable_section_key=stable_key,
                    heading_path=current_heading_path,
                    heading_level=current_level,
                    title=current_title,
                    body=body,
                    section_checksum=calculate_section_checksum(
                        heading_path=current_heading_path,
                        body=body,
                    ),
                    ordinal=len(extracted_sections),
                )
            )

            current_body_lines = []

        for line in lines:
            heading_match = _HEADING_PATTERN.match(line)

            if heading_match:
                flush_current_section()

                current_level = len(heading_match.group(1))
                current_title = heading_match.group(2).strip()

                heading_stack = [
                    (level, title)
                    for level, title in heading_stack
                    if level < current_level
                ]
                heading_stack.append((current_level, current_title))

                current_heading_path = tuple(title for _, title in heading_stack)
                current_body_lines = []
                continue

            if current_level is None:
                if line.strip():
                    current_level = 1
                    current_title = fallback_title
                    current_heading_path = (fallback_title,)
                    current_body_lines = [line]
                continue

            current_body_lines.append(line)

        flush_current_section()

        return extracted_sections

    def create_section_versions(
        self,
        *,
        document_version_id: UUID,
        content: str,
        fallback_title: str,
    ) -> list[SectionVersion]:
        extracted_sections = self.extract(
            content=content,
            fallback_title=fallback_title,
        )

        return [
            SectionVersion(
                id=uuid4(),
                document_version_id=document_version_id,
                stable_section_key=section.stable_section_key,
                heading_path=section.heading_path,
                heading_level=section.heading_level,
                title=section.title,
                body=section.body,
                section_checksum=section.section_checksum,
                ordinal=section.ordinal,
            )
            for section in extracted_sections
        ]


def build_stable_section_key(heading_path: tuple[str, ...]) -> str:
    if not heading_path:
        raise ValueError("heading_path must not be empty")

    return "/".join(slugify_heading(heading) for heading in heading_path)


def slugify_heading(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")

    return slug or "section"


def calculate_section_checksum(*, heading_path: tuple[str, ...], body: str) -> str:
    payload = "\n".join([*heading_path, body])

    return calculate_content_checksum(payload)