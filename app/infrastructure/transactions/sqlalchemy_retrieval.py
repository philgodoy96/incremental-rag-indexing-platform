from sqlalchemy.orm import Session

from app.domain.documents.repositories import VectorIndexEntryRepository
from app.infrastructure.repositories import SqlAlchemyVectorIndexEntryRepository


class SqlAlchemyRetrievalTransaction:
    def __init__(self, session: Session) -> None:
        self.vector_index_entries: VectorIndexEntryRepository = (
            SqlAlchemyVectorIndexEntryRepository(session)
        )