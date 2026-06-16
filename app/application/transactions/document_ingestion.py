from typing import Protocol

from app.domain.documents.repositories import (
    ChunkVersionRepository,
    DocumentVersionRepository,
    EmbeddingCostRecordRepository,
    EmbeddingRecordRepository,
    IngestionRunRepository,
    SectionVersionRepository,
    SourceDocumentRepository,
)


class DocumentIngestionTransaction(Protocol):
    source_documents: SourceDocumentRepository
    document_versions: DocumentVersionRepository
    section_versions: SectionVersionRepository
    chunk_versions: ChunkVersionRepository
    embedding_records: EmbeddingRecordRepository
    embedding_cost_records: EmbeddingCostRecordRepository
    ingestion_runs: IngestionRunRepository

    def flush(self) -> None:
        raise NotImplementedError

    def commit(self) -> None:
        raise NotImplementedError

    def rollback(self) -> None:
        raise NotImplementedError