from collections.abc import Generator

from app.application.services.grounded_answer_service import GroundedAnswerService
from app.application.services.semantic_retrieval_service import (
    SemanticRetrievalService,
)
from app.application.transactions.answering import AnsweringTransaction
from app.application.transactions.retrieval import RetrievalTransaction
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.transactions.sqlalchemy_retrieval import (
    SqlAlchemyRetrievalTransaction,
)
from app.providers.fake_embedding_provider import FakeEmbeddingProvider
from app.providers.fake_llm_provider import FakeLLMProvider


def get_semantic_retrieval_service() -> SemanticRetrievalService:
    return SemanticRetrievalService(provider=FakeEmbeddingProvider())


def get_grounded_answer_service() -> GroundedAnswerService:
    return GroundedAnswerService(
        retriever=SemanticRetrievalService(provider=FakeEmbeddingProvider()),
        llm_provider=FakeLLMProvider(),
    )


def get_retrieval_transaction() -> Generator[RetrievalTransaction, None, None]:
    session = SessionLocal()

    try:
        yield SqlAlchemyRetrievalTransaction(session)
    finally:
        session.close()


def get_answering_transaction() -> Generator[AnsweringTransaction, None, None]:
    session = SessionLocal()

    try:
        yield SqlAlchemyRetrievalTransaction(session)
    finally:
        session.close()
