from pathlib import Path

from app.application.services.demo_dataset_loader import DemoDatasetLoader, DemoDocumentSpec
from app.application.services.source_document_discovery import (
    SourceDocumentDiscoveryResult,
)
from app.domain.documents.enums import SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate


class DemoDatasetDiscoveryService:
    """Discovers demo dataset documents from the manifest without persisting them."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        manifest_path: Path | None = None,
        loader: DemoDatasetLoader | None = None,
    ) -> None:
        self._loader = loader or DemoDatasetLoader(
            repo_root=repo_root,
            manifest_path=manifest_path,
        )

    def discover(self) -> SourceDocumentDiscoveryResult:
        dataset = self._loader.load()

        return SourceDocumentDiscoveryResult(
            source_system=SourceSystem.DEMO_DOCUMENTS,
            source_path=dataset.manifest_path.as_posix(),
            documents=tuple(
                self._to_candidate(document)
                for document in dataset.documents
            ),
        )

    def _to_candidate(self, document: DemoDocumentSpec) -> SourceDocumentCandidate:
        candidate = SourceDocumentCandidate.create(
            source_system=SourceSystem.DEMO_DOCUMENTS,
            external_id=document.external_id,
            source_uri=document.source_uri,
            title=document.title,
            raw_content=document.content,
            tags=document.tags,
        )

        if candidate.content_checksum != document.content_checksum:
            raise ValueError(
                "demo document content checksum does not match manifest value: "
                f"{document.external_id}",
            )

        return candidate
