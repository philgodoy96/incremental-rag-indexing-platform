from sqlalchemy.orm import Session

from app.domain.documents.repositories import (
    DocumentVersionRepository,
    IngestionRunRepository,
    SourceDocumentRepository,
)
from app.infrastructure.repositories import (
    SqlAlchemyDocumentVersionRepository,
    SqlAlchemyIngestionRunRepository,
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
        self.ingestion_runs: IngestionRunRepository = SqlAlchemyIngestionRunRepository(
            session,
        )

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()