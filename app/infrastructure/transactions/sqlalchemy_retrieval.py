from sqlalchemy.orm import Session

from app.domain.documents.repositories import VectorIndexEntryRepository
from app.domain.retrieval.repositories import (
    QueryTraceHitRepository,
    QueryTraceRepository,
)
from app.infrastructure.repositories import (
    SqlAlchemyQueryTraceHitRepository,
    SqlAlchemyQueryTraceRepository,
    SqlAlchemyVectorIndexEntryRepository,
)


class SqlAlchemyRetrievalTransaction:
    def __init__(self, session: Session) -> None:
        self._session = session
        self.vector_index_entries: VectorIndexEntryRepository = (
            SqlAlchemyVectorIndexEntryRepository(session)
        )
        self.query_traces: QueryTraceRepository = SqlAlchemyQueryTraceRepository(
            session,
        )
        self.query_trace_hits: QueryTraceHitRepository = (
            SqlAlchemyQueryTraceHitRepository(session)
        )

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()
