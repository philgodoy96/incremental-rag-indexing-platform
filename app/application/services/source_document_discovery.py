from dataclasses import dataclass
from typing import Protocol

from app.domain.documents.enums import SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate


@dataclass(frozen=True, slots=True)
class SourceDocumentDiscoveryResult:
    source_system: SourceSystem
    source_path: str
    documents: tuple[SourceDocumentCandidate, ...]

    @property
    def document_count(self) -> int:
        return len(self.documents)


class SourceDocumentDiscoveryService(Protocol):
    """Discovers source document candidates without persisting them."""

    def discover(self) -> SourceDocumentDiscoveryResult: ...
