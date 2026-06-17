from typing import Protocol

from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.answering.repositories import (
    AnswerCitationRecordRepository,
    AnswerRecordRepository,
)
from app.domain.llm_observability.repositories import (
    LLMProviderCallRecordRepository,
)


class AnsweringTransaction(RetrievalTransaction, Protocol):
    answer_records: AnswerRecordRepository
    answer_citation_records: AnswerCitationRecordRepository
    llm_provider_calls: LLMProviderCallRecordRepository
