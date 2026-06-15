from dataclasses import dataclass
from pathlib import Path

from app.domain.documents.enums import SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate
from app.infrastructure.sources.local_markdown_source import LocalMarkdownSource


@dataclass(frozen=True, slots=True)
class LocalSeedDocumentDiscoveryResult:
    source_system: SourceSystem
    source_path: str
    documents: tuple[SourceDocumentCandidate, ...]

    @property
    def document_count(self) -> int:
        return len(self.documents)


class LocalSeedDocumentDiscoveryService:
    """Discovers local seed Markdown documents without persisting them."""

    def __init__(self, source_path: Path) -> None:
        self._source_path = source_path

    def discover(self) -> LocalSeedDocumentDiscoveryResult:
        source = LocalMarkdownSource(base_path=self._source_path)
        documents = tuple(source.discover())

        return LocalSeedDocumentDiscoveryResult(
            source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
            source_path=self._source_path.as_posix(),
            documents=documents,
        )