from decimal import Decimal

import pytest

from app.domain.llm_observability.usage_reports import (
    LLMUsageByModelSummary,
    LLMUsageSummary,
)


def test_llm_usage_summary_can_be_empty() -> None:
    summary = LLMUsageSummary.empty()

    assert summary.call_count == 0
    assert summary.succeeded_count == 0
    assert summary.failed_count == 0
    assert summary.prompt_tokens == 0
    assert summary.completion_tokens == 0
    assert summary.total_tokens == 0
    assert summary.estimated_cost_usd == Decimal("0")
    assert summary.average_latency_ms == 0.0


def test_llm_usage_summary_accepts_valid_aggregates() -> None:
    summary = LLMUsageSummary(
        call_count=3,
        succeeded_count=2,
        failed_count=1,
        prompt_tokens=100,
        completion_tokens=40,
        total_tokens=140,
        estimated_cost_usd=Decimal("0.0123"),
        average_latency_ms=125.5,
    )

    assert summary.call_count == 3
    assert summary.succeeded_count == 2
    assert summary.failed_count == 1
    assert summary.total_tokens == 140
    assert summary.estimated_cost_usd == Decimal("0.0123")


def test_llm_usage_summary_rejects_invalid_call_count() -> None:
    with pytest.raises(
        ValueError,
        match="call_count must equal succeeded_count plus failed_count",
    ):
        LLMUsageSummary(
            call_count=3,
            succeeded_count=3,
            failed_count=1,
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=140,
            estimated_cost_usd=Decimal("0.0123"),
            average_latency_ms=125.5,
        )


def test_llm_usage_summary_rejects_invalid_total_tokens() -> None:
    with pytest.raises(
        ValueError,
        match="total_tokens must equal prompt_tokens plus completion_tokens",
    ):
        LLMUsageSummary(
            call_count=3,
            succeeded_count=2,
            failed_count=1,
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=999,
            estimated_cost_usd=Decimal("0.0123"),
            average_latency_ms=125.5,
        )


def test_llm_usage_summary_rejects_negative_cost() -> None:
    with pytest.raises(ValueError, match="estimated_cost_usd must not be negative"):
        LLMUsageSummary(
            call_count=1,
            succeeded_count=1,
            failed_count=0,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=Decimal("-0.01"),
            average_latency_ms=10.0,
        )


def test_llm_usage_by_model_summary_accepts_valid_aggregates() -> None:
    summary = LLMUsageByModelSummary(
        provider="fake",
        model_name="fake-llm-v1",
        call_count=3,
        succeeded_count=2,
        failed_count=1,
        prompt_tokens=100,
        completion_tokens=40,
        total_tokens=140,
        estimated_cost_usd=Decimal("0.0123"),
        average_latency_ms=125.5,
    )

    assert summary.provider == "fake"
    assert summary.model_name == "fake-llm-v1"
    assert summary.call_count == 3
    assert summary.succeeded_count == 2
    assert summary.failed_count == 1


def test_llm_usage_by_model_summary_rejects_blank_provider() -> None:
    with pytest.raises(ValueError, match="provider must not be blank"):
        LLMUsageByModelSummary(
            provider=" ",
            model_name="fake-llm-v1",
            call_count=1,
            succeeded_count=1,
            failed_count=0,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=Decimal("0"),
            average_latency_ms=10.0,
        )


def test_llm_usage_by_model_summary_rejects_blank_model_name() -> None:
    with pytest.raises(ValueError, match="model_name must not be blank"):
        LLMUsageByModelSummary(
            provider="fake",
            model_name=" ",
            call_count=1,
            succeeded_count=1,
            failed_count=0,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=Decimal("0"),
            average_latency_ms=10.0,
        )