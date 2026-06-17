from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.llm_observability.enums import LLMProviderCallStatus


class LLMProviderCallResponse(BaseModel):
    id: UUID
    answer_id: UUID | None
    query_trace_id: UUID
    provider: str
    model_name: str
    status: LLMProviderCallStatus
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: str
    latency_ms: int
    started_at: datetime
    completed_at: datetime
    error_message: str | None
    created_at: datetime


class LLMProviderCallListResponse(BaseModel):
    items: list[LLMProviderCallResponse]
    limit: int
    offset: int


def decimal_to_api_string(value: Decimal) -> str:
    return format(value, "f")


def to_llm_provider_call_response(
    record: LLMProviderCallRecord,
) -> LLMProviderCallResponse:
    return LLMProviderCallResponse(
        id=record.id,
        answer_id=record.answer_id,
        query_trace_id=record.query_trace_id,
        provider=record.provider,
        model_name=record.model_name,
        status=record.status,
        prompt_tokens=record.prompt_tokens,
        completion_tokens=record.completion_tokens,
        total_tokens=record.total_tokens,
        estimated_cost_usd=decimal_to_api_string(record.estimated_cost_usd),
        latency_ms=record.latency_ms,
        started_at=record.started_at,
        completed_at=record.completed_at,
        error_message=record.error_message,
        created_at=record.created_at,
    )
