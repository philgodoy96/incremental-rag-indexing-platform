from sqlalchemy.orm import Session

from app.domain.documents.repositories import (
    ChunkVersionRepository,
    DocumentVersionRepository,
    EmbeddingCostRecordRepository,
    EmbeddingRecordRepository,
    IngestionRunRepository,
    SectionVersionRepository,
    SourceDocumentRepository,
)
from app.infrastructure.repositories import (
    SqlAlchemyChunkVersionRepository,
    SqlAlchemyDocumentVersionRepository,
    SqlAlchemyEmbeddingCostRecordRepository,
    SqlAlchemyEmbeddingRecordRepository,
    SqlAlchemyIngestionRunRepository,
    SqlAlchemySectionVersionRepository,
    SqlAlchemySourceDocumentRepository,
)


class SqlAlchemyDocumentIngestionTransaction:
    """SQLAlchemy-backed transaction boundary for document ingestion."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self.source_documents: SourceDocumentRepository = SqlAlchemySourceDocumentRepository(
            session,
        )
        self.document_versions: DocumentVersionRepository = SqlAlchemyDocumentVersionRepository(
            session,
        )
        self.section_versions: SectionVersionRepository = SqlAlchemySectionVersionRepository(
            session,
        )
        self.chunk_versions: ChunkVersionRepository = SqlAlchemyChunkVersionRepository(
            session,
        )
        self.embedding_records: EmbeddingRecordRepository = (
            SqlAlchemyEmbeddingRecordRepository(session)
        )
        self.embedding_cost_records: EmbeddingCostRecordRepository = (
            SqlAlchemyEmbeddingCostRecordRepository(session)
        )
        self.ingestion_runs: IngestionRunRepository = SqlAlchemyIngestionRunRepository(
            session,
        )

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()