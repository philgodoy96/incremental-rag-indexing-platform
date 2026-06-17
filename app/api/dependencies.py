from collections.abc import Generator

from app.application.services.semantic_retrieval_service import (
    SemanticRetrievalService,
)
from app.application.transactions.retrieval import RetrievalTransaction
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.transactions.sqlalchemy_retrieval import (
    SqlAlchemyRetrievalTransaction,
)
from app.providers.fake_embedding_provider import FakeEmbeddingProvider


def get_semantic_retrieval_service() -> SemanticRetrievalService:
    return SemanticRetrievalService(provider=FakeEmbeddingProvider())


def get_retrieval_transaction() -> Generator[RetrievalTransaction, None, None]:
    session = SessionLocal()

    try:
        yield SqlAlchemyRetrievalTransaction(session)
    finally:
        session.close()
