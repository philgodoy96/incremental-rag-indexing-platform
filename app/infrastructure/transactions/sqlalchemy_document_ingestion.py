from sqlalchemy.orm import Session

from app.domain.documents.repositories import (
    ChunkEmbeddingLinkRepository,
    ChunkVersionRepository,
    DocumentVersionRepository,
    EmbeddingCostRecordRepository,
    EmbeddingRecordRepository,
    IngestionRunRepository,
    SectionVersionRepository,
    SourceDocumentRepository,
    VectorIndexEntryRepository,
)
from app.infrastructure.repositories import (
    SqlAlchemyChunkEmbeddingLinkRepository,
    SqlAlchemyChunkVersionRepository,
    SqlAlchemyDocumentVersionRepository,
    SqlAlchemyEmbeddingCostRecordRepository,
    SqlAlchemyEmbeddingRecordRepository,
    SqlAlchemyIngestionRunRepository,
    SqlAlchemySectionVersionRepository,
    SqlAlchemySourceDocumentRepository,
    SqlAlchemyVectorIndexEntryRepository,
)


class SqlAlchemyDocumentIngestionTransaction:
    def __init__(self, session: Session) -> None:
        self._session = session

        self.source_documents: SourceDocumentRepository = (
            SqlAlchemySourceDocumentRepository(session)
        )
        self.document_versions: DocumentVersionRepository = (
            SqlAlchemyDocumentVersionRepository(session)
        )
        self.section_versions: SectionVersionRepository = (
            SqlAlchemySectionVersionRepository(session)
        )
        self.chunk_versions: ChunkVersionRepository = (
            SqlAlchemyChunkVersionRepository(session)
        )
        self.embedding_records: EmbeddingRecordRepository = (
            SqlAlchemyEmbeddingRecordRepository(session)
        )
        self.chunk_embedding_links: ChunkEmbeddingLinkRepository = (
            SqlAlchemyChunkEmbeddingLinkRepository(session)
        )
        self.vector_index_entries: VectorIndexEntryRepository = (
            SqlAlchemyVectorIndexEntryRepository(session)
        )
        self.embedding_cost_records: EmbeddingCostRecordRepository = (
            SqlAlchemyEmbeddingCostRecordRepository(session)
        )
        self.ingestion_runs: IngestionRunRepository = (
            SqlAlchemyIngestionRunRepository(session)
        )

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()