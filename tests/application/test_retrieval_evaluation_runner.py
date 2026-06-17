from dataclasses import dataclass
from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.services.retrieval_evaluation_runner import (
    RetrievalEvaluationRunner,
    SemanticSearchResultLike,
)
from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
)
from app.domain.evaluation.enums import RetrievalEvaluationCaseResultStatus
from app.domain.evaluation.repositories import (
    RetrievalEvaluationCaseResultRepository,
)
from app.domain.retrieval.entities import SemanticSearchQuery


@dataclass(frozen=True, slots=True)
class FakeRetrievedChunk:
    chunk_version_id: UUID


@dataclass(frozen=True, slots=True)
class FakeSemanticSearchResult:
    results: tuple[FakeRetrievedChunk, ...]


class FakeSemanticRetriever:
    def __init__(
        self,
        *,
        retrieved_chunk_version_ids: tuple[UUID, ...],
    ) -> None:
        self.retrieved_chunk_version_ids = retrieved_chunk_version_ids
        self.queries: list[SemanticSearchQuery] = []

    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: RetrievalTransaction,
    ) -> SemanticSearchResultLike:
        self.queries.append(query)

        return cast(
            SemanticSearchResultLike,
            FakeSemanticSearchResult(
                results=tuple(
                    FakeRetrievedChunk(chunk_version_id=chunk_version_id)
                    for chunk_version_id in self.retrieved_chunk_version_ids
                ),
            ),
        )


class FailingSemanticRetriever:
    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: RetrievalTransaction,
    ) -> SemanticSearchResultLike:
        raise RuntimeError("retrieval timeout")


class InMemoryRetrievalEvaluationCaseResultRepository(
    RetrievalEvaluationCaseResultRepository,
):
    def __init__(self) -> None:
        self.saved_results: list[RetrievalEvaluationCaseResult] = []

    def get_by_id(
        self,
        evaluation_case_result_id: UUID,
    ) -> RetrievalEvaluationCaseResult | None:
        for result in self.saved_results:
            if result.id == evaluation_case_result_id:
                return result

        return None

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> list[RetrievalEvaluationCaseResult]:
        results = list(self.saved_results)

        if status is not None:
            results = [
                result for result in results if result.status.value == status
            ]

        return results[offset : offset + limit]

    def list_by_case_id(
        self,
        evaluation_case_id: UUID,
    ) -> list[RetrievalEvaluationCaseResult]:
        return [
            result
            for result in self.saved_results
            if result.evaluation_case_id == evaluation_case_id
        ]

    def save(self, result: RetrievalEvaluationCaseResult) -> None:
        self.saved_results.append(result)

    def save_many(self, results: list[RetrievalEvaluationCaseResult]) -> None:
        self.saved_results.extend(results)


class FakeTransaction:
    def __init__(self) -> None:
        self.retrieval_evaluation_case_results = (
            InMemoryRetrievalEvaluationCaseResultRepository()
        )
        self.commit_count = 0

    def commit(self) -> None:
        self.commit_count += 1


def test_retrieval_evaluation_runner_persists_case_results_and_summary() -> None:
    expected_chunk_id = uuid4()
    unrelated_chunk_id = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
    )
    retriever = FakeSemanticRetriever(
        retrieved_chunk_version_ids=(unrelated_chunk_id, expected_chunk_id),
    )
    transaction = FakeTransaction()
    runner = RetrievalEvaluationRunner(retriever=retriever)

    run_result = runner.run_cases(
        evaluation_cases=(evaluation_case,),
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert len(run_result.results) == 1

    case_result = run_result.results[0]

    assert case_result.evaluation_case_id == evaluation_case.id
    assert case_result.status == RetrievalEvaluationCaseResultStatus.SUCCEEDED
    assert case_result.hit_count == 1
    assert case_result.recall_at_k == 1.0
    assert case_result.reciprocal_rank == 0.5

    assert run_result.summary.case_count == 1
    assert run_result.summary.succeeded_count == 1
    assert run_result.summary.failed_count == 0
    assert run_result.summary.hit_count == 1
    assert run_result.summary.total_expected_count == 1
    assert run_result.summary.hit_rate_at_k == 1.0
    assert run_result.summary.mean_recall_at_k == 1.0
    assert run_result.summary.mean_reciprocal_rank == 0.5

    assert transaction.retrieval_evaluation_case_results.saved_results == [
        case_result,
    ]
    assert transaction.commit_count == 1

    assert len(retriever.queries) == 1
    assert retriever.queries[0].query == "What is Project Atlas status?"
    assert retriever.queries[0].top_k == 5
    assert retriever.queries[0].provider == "fake"
    assert retriever.queries[0].model_name == "fake-embedding-v1"


def test_retrieval_evaluation_runner_records_failed_case_result() -> None:
    expected_chunk_id = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
    )
    retriever = FailingSemanticRetriever()
    transaction = FakeTransaction()
    runner = RetrievalEvaluationRunner(retriever=retriever)

    run_result = runner.run_cases(
        evaluation_cases=(evaluation_case,),
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert len(run_result.results) == 1

    case_result = run_result.results[0]

    assert case_result.status == RetrievalEvaluationCaseResultStatus.FAILED
    assert case_result.hit_count == 0
    assert case_result.recall_at_k == 0.0
    assert case_result.reciprocal_rank == 0.0
    assert case_result.error_message == "RuntimeError: retrieval timeout"

    assert run_result.summary.case_count == 1
    assert run_result.summary.succeeded_count == 0
    assert run_result.summary.failed_count == 1
    assert transaction.retrieval_evaluation_case_results.saved_results == [
        case_result,
    ]
    assert transaction.commit_count == 1


def test_retrieval_evaluation_runner_accepts_empty_case_set() -> None:
    retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())
    transaction = FakeTransaction()
    runner = RetrievalEvaluationRunner(retriever=retriever)

    run_result = runner.run_cases(
        evaluation_cases=(),
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert run_result.results == ()
    assert run_result.summary.case_count == 0
    assert run_result.summary.succeeded_count == 0
    assert run_result.summary.failed_count == 0
    assert run_result.summary.hit_count == 0
    assert transaction.retrieval_evaluation_case_results.saved_results == []
    assert transaction.commit_count == 1


def test_retrieval_evaluation_runner_rejects_invalid_top_k() -> None:
    retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())
    transaction = FakeTransaction()
    runner = RetrievalEvaluationRunner(retriever=retriever)

    with pytest.raises(ValueError, match="top_k must be greater than or equal to 1"):
        runner.run_cases(
            evaluation_cases=(),
            top_k=0,
            provider="fake",
            model_name="fake-embedding-v1",
            transaction=transaction,  # type: ignore[arg-type]
        )


def test_retrieval_evaluation_runner_rejects_blank_provider() -> None:
    retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())
    transaction = FakeTransaction()
    runner = RetrievalEvaluationRunner(retriever=retriever)

    with pytest.raises(ValueError, match="provider must not be blank"):
        runner.run_cases(
            evaluation_cases=(),
            top_k=5,
            provider=" ",
            model_name="fake-embedding-v1",
            transaction=transaction,  # type: ignore[arg-type]
        )


def test_retrieval_evaluation_runner_rejects_blank_model_name() -> None:
    retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())
    transaction = FakeTransaction()
    runner = RetrievalEvaluationRunner(retriever=retriever)

    with pytest.raises(ValueError, match="model_name must not be blank"):
        runner.run_cases(
            evaluation_cases=(),
            top_k=5,
            provider="fake",
            model_name=" ",
            transaction=transaction,  # type: ignore[arg-type]
        )