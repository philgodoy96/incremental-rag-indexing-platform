from typing import Protocol

from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.answering.repositories import (
    AnswerCitationRecordRepository,
    AnswerRecordRepository,
)


class AnsweringTransaction(RetrievalTransaction, Protocol):
    answer_records: AnswerRecordRepository
    answer_citation_records: AnswerCitationRecordRepository
