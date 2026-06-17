from uuid import UUID

from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
)
from app.domain.evaluation.enums import RetrievalEvaluationCaseResultStatus
from app.infrastructure.db.models import (
    RetrievalEvaluationCaseModel,
    RetrievalEvaluationCaseResultModel,
)


def _uuid_tuple_from_json(value: list[str]) -> tuple[UUID, ...]:
    return tuple(UUID(item) for item in value)


def _uuid_tuple_to_json(value: tuple[UUID, ...]) -> list[str]:
    return [str(item) for item in value]


def retrieval_evaluation_case_to_model(
    entity: RetrievalEvaluationCase,
) -> RetrievalEvaluationCaseModel:
    model = RetrievalEvaluationCaseModel()

    model.id = entity.id
    model.name = entity.name
    model.query = entity.query
    model.expected_chunk_version_ids = _uuid_tuple_to_json(
        entity.expected_chunk_version_ids,
    )
    model.tags = list(entity.tags)
    model.created_at = entity.created_at

    return model


def retrieval_evaluation_case_from_model(
    model: RetrievalEvaluationCaseModel,
) -> RetrievalEvaluationCase:
    return RetrievalEvaluationCase(
        id=model.id,
        name=model.name,
        query=model.query,
        expected_chunk_version_ids=_uuid_tuple_from_json(
            model.expected_chunk_version_ids,
        ),
        tags=tuple(model.tags),
        created_at=model.created_at,
    )


def retrieval_evaluation_case_result_to_model(
    entity: RetrievalEvaluationCaseResult,
) -> RetrievalEvaluationCaseResultModel:
    model = RetrievalEvaluationCaseResultModel()

    model.id = entity.id
    model.evaluation_case_id = entity.evaluation_case_id
    model.query = entity.query
    model.expected_chunk_version_ids = _uuid_tuple_to_json(
        entity.expected_chunk_version_ids,
    )
    model.retrieved_chunk_version_ids = _uuid_tuple_to_json(
        entity.retrieved_chunk_version_ids,
    )
    model.status = entity.status.value
    model.top_k = entity.top_k
    model.hit_count = entity.hit_count
    model.recall_at_k = entity.recall_at_k
    model.reciprocal_rank = entity.reciprocal_rank
    model.error_message = entity.error_message
    model.created_at = entity.created_at

    return model


def retrieval_evaluation_case_result_from_model(
    model: RetrievalEvaluationCaseResultModel,
) -> RetrievalEvaluationCaseResult:
    return RetrievalEvaluationCaseResult(
        id=model.id,
        evaluation_case_id=model.evaluation_case_id,
        query=model.query,
        expected_chunk_version_ids=_uuid_tuple_from_json(
            model.expected_chunk_version_ids,
        ),
        retrieved_chunk_version_ids=_uuid_tuple_from_json(
            model.retrieved_chunk_version_ids,
        ),
        status=RetrievalEvaluationCaseResultStatus(model.status),
        top_k=model.top_k,
        hit_count=model.hit_count,
        recall_at_k=model.recall_at_k,
        reciprocal_rank=model.reciprocal_rank,
        error_message=model.error_message,
        created_at=model.created_at,
    )