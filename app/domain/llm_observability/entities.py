from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.llm_observability.enums import LLMProviderCallStatus


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_timezone_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class LLMProviderCallRecord:
    id: UUID
    answer_id: UUID | None
    query_trace_id: UUID
    provider: str
    model_name: str
    status: LLMProviderCallStatus
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: Decimal
    latency_ms: int
    started_at: datetime
    completed_at: datetime
    error_message: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")
        ensure_timezone_aware(self.started_at, "started_at")
        ensure_timezone_aware(self.completed_at, "completed_at")
        ensure_timezone_aware(self.created_at, "created_at")

        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must not be negative")

        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must not be negative")

        if self.total_tokens < 0:
            raise ValueError("total_tokens must not be negative")

        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError(
                "total_tokens must equal prompt_tokens plus completion_tokens",
            )

        if self.estimated_cost_usd < Decimal("0"):
            raise ValueError("estimated_cost_usd must not be negative")

        if self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")

        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not be before started_at")

        if self.status == LLMProviderCallStatus.FAILED and not self.error_message:
            raise ValueError("failed provider call must include error_message")

        if self.status == LLMProviderCallStatus.SUCCEEDED and self.error_message:
            raise ValueError("succeeded provider call must not include error_message")

    @classmethod
    def succeeded(
        cls,
        *,
        answer_id: UUID | None,
        query_trace_id: UUID,
        provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost_usd: Decimal,
        started_at: datetime,
        completed_at: datetime,
    ) -> "LLMProviderCallRecord":
        latency_ms = int((completed_at - started_at).total_seconds() * 1000)

        return cls(
            id=uuid4(),
            answer_id=answer_id,
            query_trace_id=query_trace_id,
            provider=provider,
            model_name=model_name,
            status=LLMProviderCallStatus.SUCCEEDED,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=estimated_cost_usd,
            latency_ms=latency_ms,
            started_at=started_at,
            completed_at=completed_at,
        )

    @classmethod
    def failed(
        cls,
        *,
        answer_id: UUID | None,
        query_trace_id: UUID,
        provider: str,
        model_name: str,
        error_message: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> "LLMProviderCallRecord":
        ensure_not_blank(error_message, "error_message")

        latency_ms = int((completed_at - started_at).total_seconds() * 1000)

        return cls(
            id=uuid4(),
            answer_id=answer_id,
            query_trace_id=query_trace_id,
            provider=provider,
            model_name=model_name,
            status=LLMProviderCallStatus.FAILED,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost_usd=Decimal("0"),
            latency_ms=latency_ms,
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
        )