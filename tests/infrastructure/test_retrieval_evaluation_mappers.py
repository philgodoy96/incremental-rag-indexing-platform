from uuid import uuid4

from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
)
from app.domain.evaluation.enums import RetrievalEvaluationCaseResultStatus
from app.infrastructure.db.mappers import (
    retrieval_evaluation_case_from_model,
    retrieval_evaluation_case_result_from_model,
    retrieval_evaluation_case_result_to_model,
    retrieval_evaluation_case_to_model,
)


def test_retrieval_evaluation_case_mapper_round_trips_entity() -> None:
    expected_chunk_id = uuid4()

    evaluation_case = RetrievalEvaluationCase.create(
        name="Project Atlas status",
        query="What is Project Atlas status?",
        expected_chunk_version_ids=(expected_chunk_id,),
        tags=("status", "project-atlas"),
    )

    model = retrieval_evaluation_case_to_model(evaluation_case)
    mapped_case = retrieval_evaluation_case_from_model(model)

    assert mapped_case == evaluation_case


def test_retrieval_evaluation_case_result_mapper_round_trips_succeeded_entity() -> None:
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

    model = retrieval_evaluation_case_result_to_model(result)
    mapped_result = retrieval_evaluation_case_result_from_model(model)

    assert mapped_result == result
    assert mapped_result.status == RetrievalEvaluationCaseResultStatus.SUCCEEDED


def test_retrieval_evaluation_case_result_mapper_round_trips_failed_entity() -> None:
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

    model = retrieval_evaluation_case_result_to_model(result)
    mapped_result = retrieval_evaluation_case_result_from_model(model)

    assert mapped_result == result
    assert mapped_result.status == RetrievalEvaluationCaseResultStatus.FAILED
    assert mapped_result.error_message == "retrieval timeout"