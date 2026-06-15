from pathlib import Path

from app.domain.documents.enums import SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate


class LocalMarkdownSource:
    """Discovers Markdown files from a local directory."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def discover(self) -> list[SourceDocumentCandidate]:
        if not self._base_path.exists():
            return []

        candidates: list[SourceDocumentCandidate] = []

        for file_path in sorted(self._base_path.rglob("*.md")):
            if not file_path.is_file():
                continue

            raw_content = file_path.read_text(encoding="utf-8")

            if not raw_content.strip():
                continue

            relative_path = file_path.relative_to(self._base_path)
            external_id = relative_path.as_posix()
            source_uri = self._build_source_uri(relative_path)
            title = extract_markdown_title(raw_content, fallback=file_path.stem)

            candidates.append(
                SourceDocumentCandidate.create(
                    source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
                    external_id=external_id,
                    source_uri=source_uri,
                    title=title,
                    raw_content=raw_content,
                )
            )

        return candidates

    def _build_source_uri(self, relative_path: Path) -> str:
        return (Path("seed_documents") / relative_path).as_posix()


def extract_markdown_title(content: str, *, fallback: str) -> str:
    """Extract the first H1 heading as title.

    If no H1 is found, fall back to the file stem.
    """

    for line in content.splitlines():
        stripped_line = line.strip()

        if stripped_line.startswith("# ") and len(stripped_line) > 2:
            return stripped_line[2:].strip()

    return fallback.replace("-", " ").replace("_", " ").title()