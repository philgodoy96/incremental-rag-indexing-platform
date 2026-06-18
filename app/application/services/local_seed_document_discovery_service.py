from pathlib import Path

from app.application.services.source_document_discovery import (
    SourceDocumentDiscoveryResult,
)
from app.domain.documents.enums import SourceSystem
from app.infrastructure.sources.local_markdown_source import LocalMarkdownSource

LocalSeedDocumentDiscoveryResult = SourceDocumentDiscoveryResult


class LocalSeedDocumentDiscoveryService:
    """Discovers local seed Markdown documents without persisting them."""

    def __init__(self, source_path: Path) -> None:
        self._source_path = source_path

    def discover(self) -> SourceDocumentDiscoveryResult:
        source = LocalMarkdownSource(base_path=self._source_path)
        documents = tuple(source.discover())

        return SourceDocumentDiscoveryResult(
            source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
            source_path=self._source_path.as_posix(),
            documents=documents,
        )
