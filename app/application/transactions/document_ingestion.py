from typing import Protocol

from app.domain.documents.repositories import (
    DocumentVersionRepository,
    IngestionRunRepository,
    SourceDocumentRepository,
)


class DocumentIngestionTransaction(Protocol):
    source_documents: SourceDocumentRepository
    document_versions: DocumentVersionRepository
    ingestion_runs: IngestionRunRepository

    def commit(self) -> None:
        raise NotImplementedError

    def rollback(self) -> None:
        raise NotImplementedError