from typing import Protocol

from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.evaluation.repositories import (
    RetrievalEvaluationCaseRepository,
    RetrievalEvaluationCaseResultRepository,
)


class EvaluationTransaction(RetrievalTransaction, Protocol):
    retrieval_evaluation_cases: RetrievalEvaluationCaseRepository
    retrieval_evaluation_case_results: RetrievalEvaluationCaseResultRepository