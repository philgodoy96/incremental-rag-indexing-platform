from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
    RetrievalEvaluationRunSummary,
)
from app.domain.evaluation.enums import RetrievalEvaluationCaseResultStatus


class RetrievalEvaluationCaseCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    query: str = Field(min_length=1)
    expected_chunk_version_ids: list[UUID] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class RetrievalEvaluationCaseResponse(BaseModel):
    id: UUID
    name: str
    query: str
    expected_chunk_version_ids: list[UUID]
    tags: list[str]
    created_at: datetime


class RetrievalEvaluationCaseListResponse(BaseModel):
    items: list[RetrievalEvaluationCaseResponse]
    limit: int
    offset: int


class RetrievalEvaluationCaseResultResponse(BaseModel):
    id: UUID
    evaluation_case_id: UUID
    query: str
    expected_chunk_version_ids: list[UUID]
    retrieved_chunk_version_ids: list[UUID]
    status: RetrievalEvaluationCaseResultStatus
    top_k: int
    hit_count: int
    recall_at_k: float
    reciprocal_rank: float
    error_message: str | None
    created_at: datetime


class RetrievalEvaluationCaseResultListResponse(BaseModel):
    items: list[RetrievalEvaluationCaseResultResponse]
    limit: int
    offset: int


class RetrievalEvaluationRunRequest(BaseModel):
    evaluation_case_ids: list[UUID] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    provider: str = Field(default="fake", min_length=1)
    model_name: str = Field(default="fake-embedding-v1", min_length=1)


class RetrievalEvaluationRunSummaryResponse(BaseModel):
    case_count: int
    succeeded_count: int
    failed_count: int
    hit_count: int
    total_expected_count: int
    hit_rate_at_k: float
    mean_recall_at_k: float
    mean_reciprocal_rank: float


class RetrievalEvaluationRunResponse(BaseModel):
    results: list[RetrievalEvaluationCaseResultResponse]
    summary: RetrievalEvaluationRunSummaryResponse


def to_retrieval_evaluation_case_response(
    evaluation_case: RetrievalEvaluationCase,
) -> RetrievalEvaluationCaseResponse:
    return RetrievalEvaluationCaseResponse(
        id=evaluation_case.id,
        name=evaluation_case.name,
        query=evaluation_case.query,
        expected_chunk_version_ids=list(
            evaluation_case.expected_chunk_version_ids,
        ),
        tags=list(evaluation_case.tags),
        created_at=evaluation_case.created_at,
    )


def to_retrieval_evaluation_case_result_response(
    result: RetrievalEvaluationCaseResult,
) -> RetrievalEvaluationCaseResultResponse:
    return RetrievalEvaluationCaseResultResponse(
        id=result.id,
        evaluation_case_id=result.evaluation_case_id,
        query=result.query,
        expected_chunk_version_ids=list(result.expected_chunk_version_ids),
        retrieved_chunk_version_ids=list(result.retrieved_chunk_version_ids),
        status=result.status,
        top_k=result.top_k,
        hit_count=result.hit_count,
        recall_at_k=result.recall_at_k,
        reciprocal_rank=result.reciprocal_rank,
        error_message=result.error_message,
        created_at=result.created_at,
    )


def to_retrieval_evaluation_run_summary_response(
    summary: RetrievalEvaluationRunSummary,
) -> RetrievalEvaluationRunSummaryResponse:
    return RetrievalEvaluationRunSummaryResponse(
        case_count=summary.case_count,
        succeeded_count=summary.succeeded_count,
        failed_count=summary.failed_count,
        hit_count=summary.hit_count,
        total_expected_count=summary.total_expected_count,
        hit_rate_at_k=summary.hit_rate_at_k,
        mean_recall_at_k=summary.mean_recall_at_k,
        mean_reciprocal_rank=summary.mean_reciprocal_rank,
    )