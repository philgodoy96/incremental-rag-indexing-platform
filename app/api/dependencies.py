from collections.abc import Generator
from decimal import Decimal

from app.application.configuration.llm_provider_settings import (
    LLMProviderRuntimeSettings,
)
from app.application.services.grounded_answer_service import GroundedAnswerService
from app.application.services.semantic_retrieval_service import (
    SemanticRetrievalService,
)
from app.application.transactions.answering import AnsweringTransaction
from app.application.transactions.retrieval import RetrievalTransaction
from app.config.settings import get_settings
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.transactions.sqlalchemy_retrieval import (
    SqlAlchemyRetrievalTransaction,
)
from app.providers.fake_embedding_provider import FakeEmbeddingProvider
from app.providers.llm import LLMProvider
from app.providers.llm_provider_factory import build_llm_provider


def get_semantic_retrieval_service() -> SemanticRetrievalService:
    return SemanticRetrievalService(provider=FakeEmbeddingProvider())


def get_llm_provider() -> LLMProvider:
    settings = get_settings()

    runtime_settings = LLMProviderRuntimeSettings(
        provider=settings.llm_provider,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        openai_timeout_seconds=settings.openai_timeout_seconds,
        openai_max_output_tokens=settings.openai_max_output_tokens,
        openai_input_price_per_1m_tokens_usd=Decimal(
            str(settings.openai_input_price_per_1m_tokens_usd),
        ),
        openai_output_price_per_1m_tokens_usd=Decimal(
            str(settings.openai_output_price_per_1m_tokens_usd),
        ),
    )

    return build_llm_provider(runtime_settings)


def get_grounded_answer_service() -> GroundedAnswerService:
    return GroundedAnswerService(
        retriever=SemanticRetrievalService(provider=FakeEmbeddingProvider()),
        llm_provider=get_llm_provider(),
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
