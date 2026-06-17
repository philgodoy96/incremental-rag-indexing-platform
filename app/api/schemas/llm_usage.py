from decimal import Decimal

from pydantic import BaseModel

from app.domain.llm_observability.usage_reports import (
    LLMUsageByModelSummary,
    LLMUsageSummary,
)


class LLMUsageSummaryResponse(BaseModel):
    call_count: int
    succeeded_count: int
    failed_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: str
    average_latency_ms: float


class LLMUsageByModelSummaryResponse(LLMUsageSummaryResponse):
    provider: str
    model_name: str


class LLMUsageByModelListResponse(BaseModel):
    items: list[LLMUsageByModelSummaryResponse]


def decimal_to_api_string(value: Decimal) -> str:
    return format(value, "f")


def to_llm_usage_summary_response(
    summary: LLMUsageSummary,
) -> LLMUsageSummaryResponse:
    return LLMUsageSummaryResponse(
        call_count=summary.call_count,
        succeeded_count=summary.succeeded_count,
        failed_count=summary.failed_count,
        prompt_tokens=summary.prompt_tokens,
        completion_tokens=summary.completion_tokens,
        total_tokens=summary.total_tokens,
        estimated_cost_usd=decimal_to_api_string(summary.estimated_cost_usd),
        average_latency_ms=summary.average_latency_ms,
    )


def to_llm_usage_by_model_summary_response(
    summary: LLMUsageByModelSummary,
) -> LLMUsageByModelSummaryResponse:
    return LLMUsageByModelSummaryResponse(
        provider=summary.provider,
        model_name=summary.model_name,
        call_count=summary.call_count,
        succeeded_count=summary.succeeded_count,
        failed_count=summary.failed_count,
        prompt_tokens=summary.prompt_tokens,
        completion_tokens=summary.completion_tokens,
        total_tokens=summary.total_tokens,
        estimated_cost_usd=decimal_to_api_string(summary.estimated_cost_usd),
        average_latency_ms=summary.average_latency_ms,
    )