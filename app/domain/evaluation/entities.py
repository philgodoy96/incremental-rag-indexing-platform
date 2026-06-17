from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.evaluation.enums import RetrievalEvaluationCaseResultStatus


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_timezone_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def ensure_ratio(value: float, field_name: str) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationCase:
    id: UUID
    name: str
    query: str
    expected_chunk_version_ids: tuple[UUID, ...]
    tags: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        ensure_not_blank(self.name, "name")
        ensure_not_blank(self.query, "query")
        ensure_timezone_aware(self.created_at, "created_at")

        if not self.expected_chunk_version_ids:
            raise ValueError("expected_chunk_version_ids must not be empty")

        for tag in self.tags:
            ensure_not_blank(tag, "tag")

    @classmethod
    def create(
        cls,
        *,
        name: str,
        query: str,
        expected_chunk_version_ids: tuple[UUID, ...],
        tags: tuple[str, ...] = (),
    ) -> "RetrievalEvaluationCase":
        return cls(
            id=uuid4(),
            name=name,
            query=query,
            expected_chunk_version_ids=expected_chunk_version_ids,
            tags=tags,
        )


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationCaseResult:
    id: UUID
    evaluation_case_id: UUID
    query: str
    expected_chunk_version_ids: tuple[UUID, ...]
    retrieved_chunk_version_ids: tuple[UUID, ...]
    status: RetrievalEvaluationCaseResultStatus
    top_k: int
    hit_count: int
    recall_at_k: float
    reciprocal_rank: float
    error_message: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        ensure_not_blank(self.query, "query")
        ensure_timezone_aware(self.created_at, "created_at")

        if not self.expected_chunk_version_ids:
            raise ValueError("expected_chunk_version_ids must not be empty")

        if self.top_k < 1:
            raise ValueError("top_k must be greater than or equal to 1")

        if self.hit_count < 0:
            raise ValueError("hit_count must not be negative")

        if self.hit_count > len(self.expected_chunk_version_ids):
            raise ValueError("hit_count must not exceed expected chunk count")

        ensure_ratio(self.recall_at_k, "recall_at_k")
        ensure_ratio(self.reciprocal_rank, "reciprocal_rank")

        if (
            self.status == RetrievalEvaluationCaseResultStatus.FAILED
            and not self.error_message
        ):
            raise ValueError("failed evaluation case result must include error_message")

        if (
            self.status == RetrievalEvaluationCaseResultStatus.SUCCEEDED
            and self.error_message
        ):
            raise ValueError(
                "succeeded evaluation case result must not include error_message",
            )

    @classmethod
    def succeeded(
        cls,
        *,
        evaluation_case: RetrievalEvaluationCase,
        retrieved_chunk_version_ids: tuple[UUID, ...],
        top_k: int,
    ) -> "RetrievalEvaluationCaseResult":
        expected_ids = set(evaluation_case.expected_chunk_version_ids)
        retrieved_ids = list(retrieved_chunk_version_ids)

        hit_ids = expected_ids.intersection(retrieved_ids)
        hit_count = len(hit_ids)
        recall_at_k = hit_count / len(expected_ids)

        reciprocal_rank = 0.0

        for rank, chunk_version_id in enumerate(retrieved_ids, start=1):
            if chunk_version_id in expected_ids:
                reciprocal_rank = 1 / rank
                break

        return cls(
            id=uuid4(),
            evaluation_case_id=evaluation_case.id,
            query=evaluation_case.query,
            expected_chunk_version_ids=evaluation_case.expected_chunk_version_ids,
            retrieved_chunk_version_ids=retrieved_chunk_version_ids,
            status=RetrievalEvaluationCaseResultStatus.SUCCEEDED,
            top_k=top_k,
            hit_count=hit_count,
            recall_at_k=recall_at_k,
            reciprocal_rank=reciprocal_rank,
        )

    @classmethod
    def failed(
        cls,
        *,
        evaluation_case: RetrievalEvaluationCase,
        top_k: int,
        error_message: str,
    ) -> "RetrievalEvaluationCaseResult":
        ensure_not_blank(error_message, "error_message")

        return cls(
            id=uuid4(),
            evaluation_case_id=evaluation_case.id,
            query=evaluation_case.query,
            expected_chunk_version_ids=evaluation_case.expected_chunk_version_ids,
            retrieved_chunk_version_ids=(),
            status=RetrievalEvaluationCaseResultStatus.FAILED,
            top_k=top_k,
            hit_count=0,
            recall_at_k=0.0,
            reciprocal_rank=0.0,
            error_message=error_message,
        )


@dataclass(frozen=True, slots=True)
class RetrievalEvaluationRunSummary:
    case_count: int
    succeeded_count: int
    failed_count: int
    hit_count: int
    total_expected_count: int
    hit_rate_at_k: float
    mean_recall_at_k: float
    mean_reciprocal_rank: float

    def __post_init__(self) -> None:
        if self.case_count < 0:
            raise ValueError("case_count must not be negative")

        if self.succeeded_count < 0:
            raise ValueError("succeeded_count must not be negative")

        if self.failed_count < 0:
            raise ValueError("failed_count must not be negative")

        if self.case_count != self.succeeded_count + self.failed_count:
            raise ValueError(
                "case_count must equal succeeded_count plus failed_count",
            )

        if self.hit_count < 0:
            raise ValueError("hit_count must not be negative")

        if self.total_expected_count < 0:
            raise ValueError("total_expected_count must not be negative")

        if self.hit_count > self.total_expected_count:
            raise ValueError("hit_count must not exceed total_expected_count")

        ensure_ratio(self.hit_rate_at_k, "hit_rate_at_k")
        ensure_ratio(self.mean_recall_at_k, "mean_recall_at_k")
        ensure_ratio(self.mean_reciprocal_rank, "mean_reciprocal_rank")

    @classmethod
    def from_case_results(
        cls,
        results: tuple[RetrievalEvaluationCaseResult, ...],
    ) -> "RetrievalEvaluationRunSummary":
        if not results:
            return cls(
                case_count=0,
                succeeded_count=0,
                failed_count=0,
                hit_count=0,
                total_expected_count=0,
                hit_rate_at_k=0.0,
                mean_recall_at_k=0.0,
                mean_reciprocal_rank=0.0,
            )

        succeeded_results = [
            result
            for result in results
            if result.status == RetrievalEvaluationCaseResultStatus.SUCCEEDED
        ]
        failed_results = [
            result
            for result in results
            if result.status == RetrievalEvaluationCaseResultStatus.FAILED
        ]

        hit_count = sum(result.hit_count for result in results)
        total_expected_count = sum(
            len(result.expected_chunk_version_ids)
            for result in results
        )

        cases_with_at_least_one_hit = sum(
            1
            for result in results
            if result.hit_count > 0
        )

        return cls(
            case_count=len(results),
            succeeded_count=len(succeeded_results),
            failed_count=len(failed_results),
            hit_count=hit_count,
            total_expected_count=total_expected_count,
            hit_rate_at_k=cases_with_at_least_one_hit / len(results),
            mean_recall_at_k=sum(result.recall_at_k for result in results)
            / len(results),
            mean_reciprocal_rank=sum(
                result.reciprocal_rank
                for result in results
            )
            / len(results),
        )