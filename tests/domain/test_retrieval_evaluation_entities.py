from uuid import uuid4

import pytest

from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
    RetrievalEvaluationRunSummary,
)
from app.domain.evaluation.enums import RetrievalEvaluationCaseResultStatus


def test_retrieval_evaluation_case_can_be_created() -> None:
    expected_chunk_id = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
        tags=("status", "project-atlas"),
    )

    assert evaluation_case.name == "Project Atlas status"
    assert evaluation_case.query == "What is Project Atlas status?"
    assert evaluation_case.expected_chunk_version_ids == (expected_chunk_id,)
    assert evaluation_case.tags == ("status", "project-atlas")


def test_retrieval_evaluation_case_rejects_empty_expected_chunks() -> None:
    with pytest.raises(
        ValueError,
        match="expected_chunk_version_ids must not be empty",
    ):
        RetrievalEvaluationCase.create(
            name="Project Atlas status",
            query="What is Project Atlas status?",
            expected_chunk_version_ids=(),
        )


def test_retrieval_evaluation_case_result_computes_perfect_match_metrics() -> None:
    expected_chunk_id = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
    )

    result = RetrievalEvaluationCaseResult.succeeded(
        evaluation_case=evaluation_case,
        retrieved_chunk_version_ids=(expected_chunk_id,),
        top_k=5,
    )

    assert result.status == RetrievalEvaluationCaseResultStatus.SUCCEEDED
    assert result.hit_count == 1
    assert result.recall_at_k == 1.0
    assert result.reciprocal_rank == 1.0
    assert result.error_message is None


def test_retrieval_evaluation_case_result_computes_partial_match_metrics() -> None:
    expected_first = uuid4()
    expected_second = uuid4()
    unrelated = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_first, expected_second),
    )

    result = RetrievalEvaluationCaseResult.succeeded(
        evaluation_case=evaluation_case,
        retrieved_chunk_version_ids=(unrelated, expected_second),
        top_k=5,
    )

    assert result.hit_count == 1
    assert result.recall_at_k == 0.5
    assert result.reciprocal_rank == 0.5


def test_retrieval_evaluation_case_result_computes_no_hit_metrics() -> None:
    expected_chunk_id = uuid4()
    unrelated = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
    )

    result = RetrievalEvaluationCaseResult.succeeded(
        evaluation_case=evaluation_case,
        retrieved_chunk_version_ids=(unrelated,),
        top_k=5,
    )

    assert result.hit_count == 0
    assert result.recall_at_k == 0.0
    assert result.reciprocal_rank == 0.0


def test_failed_retrieval_evaluation_case_result_requires_error_message() -> None:
    expected_chunk_id = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
    )

    with pytest.raises(
        ValueError,
        match="error_message must not be blank",
    ):
        RetrievalEvaluationCaseResult.failed(
            evaluation_case=evaluation_case,
            top_k=5,
            error_message=" ",
        )


def test_retrieval_evaluation_case_result_can_be_failed() -> None:
    expected_chunk_id = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
    )

    result = RetrievalEvaluationCaseResult.failed(
        evaluation_case=evaluation_case,
        top_k=5,
        error_message="retrieval timeout",
    )

    assert result.status == RetrievalEvaluationCaseResultStatus.FAILED
    assert result.hit_count == 0
    assert result.recall_at_k == 0.0
    assert result.reciprocal_rank == 0.0
    assert result.error_message == "retrieval timeout"


def test_retrieval_evaluation_run_summary_can_be_empty() -> None:
    summary = RetrievalEvaluationRunSummary.from_case_results(())

    assert summary.case_count == 0
    assert summary.succeeded_count == 0
    assert summary.failed_count == 0
    assert summary.hit_count == 0
    assert summary.total_expected_count == 0
    assert summary.hit_rate_at_k == 0.0
    assert summary.mean_recall_at_k == 0.0
    assert summary.mean_reciprocal_rank == 0.0


def test_retrieval_evaluation_run_summary_computes_aggregate_metrics() -> None:
    expected_first = uuid4()
    expected_second = uuid4()
    unrelated = uuid4()

    first_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_first,),
    )
    second_case = RetrievalEvaluationCase.create(
        name="Project Atlas owner",
        query="Who owns Project Atlas?",
        expected_chunk_version_ids=(expected_second,),
    )

    first_result = RetrievalEvaluationCaseResult.succeeded(
        evaluation_case=first_case,
        retrieved_chunk_version_ids=(expected_first,),
        top_k=5,
    )
    second_result = RetrievalEvaluationCaseResult.succeeded(
        evaluation_case=second_case,
        retrieved_chunk_version_ids=(unrelated,),
        top_k=5,
    )

    summary = RetrievalEvaluationRunSummary.from_case_results(
        (first_result, second_result),
    )

    assert summary.case_count == 2
    assert summary.succeeded_count == 2
    assert summary.failed_count == 0
    assert summary.hit_count == 1
    assert summary.total_expected_count == 2
    assert summary.hit_rate_at_k == 0.5
    assert summary.mean_recall_at_k == 0.5
    assert summary.mean_reciprocal_rank == 0.5


def test_retrieval_evaluation_run_summary_counts_failed_cases() -> None:
    expected_first = uuid4()
    expected_second = uuid4()

    first_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_first,),
    )
    second_case = RetrievalEvaluationCase.create(
        name="Project Atlas owner",
        query="Who owns Project Atlas?",
        expected_chunk_version_ids=(expected_second,),
    )

    first_result = RetrievalEvaluationCaseResult.succeeded(
        evaluation_case=first_case,
        retrieved_chunk_version_ids=(expected_first,),
        top_k=5,
    )
    second_result = RetrievalEvaluationCaseResult.failed(
        evaluation_case=second_case,
        top_k=5,
        error_message="retrieval timeout",
    )

    summary = RetrievalEvaluationRunSummary.from_case_results(
        (first_result, second_result),
    )

    assert summary.case_count == 2
    assert summary.succeeded_count == 1
    assert summary.failed_count == 1
    assert summary.hit_count == 1
    assert summary.total_expected_count == 2
    assert summary.hit_rate_at_k == 0.5
    assert summary.mean_recall_at_k == 0.5
    assert summary.mean_reciprocal_rank == 0.5