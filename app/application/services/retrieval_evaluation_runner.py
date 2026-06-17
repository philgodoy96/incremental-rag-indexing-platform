from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.application.transactions.evaluation import EvaluationTransaction
from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
    RetrievalEvaluationRunSummary,
)
from app.domain.retrieval.entities import SemanticSearchQuery


class RetrievedChunkLike(Protocol):
    chunk_version_id: UUID


class SemanticSearchResultLike(Protocol):
    results: tuple[RetrievedChunkLike, ...]


class SemanticRetriever(Protocol):
    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: RetrievalTransaction,
    ) -> SemanticSearchResultLike:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationRunResult:
    results: tuple[RetrievalEvaluationCaseResult, ...]
    summary: RetrievalEvaluationRunSummary


class RetrievalEvaluationRunner:
    def __init__(self, *, retriever: SemanticRetriever) -> None:
        self._retriever = retriever

    def run_cases(
        self,
        *,
        evaluation_cases: tuple[RetrievalEvaluationCase, ...],
        top_k: int,
        provider: str,
        model_name: str,
        transaction: EvaluationTransaction,
    ) -> RetrievalEvaluationRunResult:
        if top_k < 1:
            raise ValueError("top_k must be greater than or equal to 1")

        if not provider or not provider.strip():
            raise ValueError("provider must not be blank")

        if not model_name or not model_name.strip():
            raise ValueError("model_name must not be blank")

        results = tuple(
            self._run_single_case(
                evaluation_case=evaluation_case,
                top_k=top_k,
                provider=provider,
                model_name=model_name,
                transaction=transaction,
            )
            for evaluation_case in evaluation_cases
        )

        transaction.retrieval_evaluation_case_results.save_many(list(results))
        transaction.commit()

        return RetrievalEvaluationRunResult(
            results=results,
            summary=RetrievalEvaluationRunSummary.from_case_results(results),
        )

    def _run_single_case(
        self,
        *,
        evaluation_case: RetrievalEvaluationCase,
        top_k: int,
        provider: str,
        model_name: str,
        transaction: EvaluationTransaction,
    ) -> RetrievalEvaluationCaseResult:
        try:
            retrieval_result = self._retriever.search(
                query=SemanticSearchQuery(
                    query=evaluation_case.query,
                    top_k=top_k,
                    provider=provider,
                    model_name=model_name,
                ),
                transaction=transaction,
            )

            retrieved_chunk_version_ids = tuple(
                chunk.chunk_version_id
                for chunk in retrieval_result.results
            )

            return RetrievalEvaluationCaseResult.succeeded(
                evaluation_case=evaluation_case,
                retrieved_chunk_version_ids=retrieved_chunk_version_ids,
                top_k=top_k,
            )
        except Exception as error:
            return RetrievalEvaluationCaseResult.failed(
                evaluation_case=evaluation_case,
                top_k=top_k,
                error_message=f"{type(error).__name__}: {error}",
            )