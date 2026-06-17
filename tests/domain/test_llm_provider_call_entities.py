from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.llm_observability.enums import LLMProviderCallStatus


def test_llm_provider_call_record_can_be_marked_succeeded() -> None:
    started_at = datetime.now(UTC)
    completed_at = started_at + timedelta(milliseconds=125)

    record = LLMProviderCallRecord.succeeded(
        answer_id=uuid4(),
        query_trace_id=uuid4(),
        provider="fake",
        model_name="fake-llm-v1",
        prompt_tokens=10,
        completion_tokens=5,
        estimated_cost_usd=Decimal("0.0001"),
        started_at=started_at,
        completed_at=completed_at,
    )

    assert record.status == LLMProviderCallStatus.SUCCEEDED
    assert record.prompt_tokens == 10
    assert record.completion_tokens == 5
    assert record.total_tokens == 15
    assert record.estimated_cost_usd == Decimal("0.0001")
    assert record.latency_ms == 125
    assert record.error_message is None


def test_llm_provider_call_record_can_be_marked_failed() -> None:
    started_at = datetime.now(UTC)
    completed_at = started_at + timedelta(milliseconds=50)

    record = LLMProviderCallRecord.failed(
        answer_id=None,
        query_trace_id=uuid4(),
        provider="fake",
        model_name="fake-llm-v1",
        error_message="provider timeout",
        started_at=started_at,
        completed_at=completed_at,
    )

    assert record.status == LLMProviderCallStatus.FAILED
    assert record.prompt_tokens == 0
    assert record.completion_tokens == 0
    assert record.total_tokens == 0
    assert record.estimated_cost_usd == Decimal("0")
    assert record.latency_ms == 50
    assert record.error_message == "provider timeout"


def test_llm_provider_call_record_rejects_invalid_total_tokens() -> None:
    now = datetime.now(UTC)

    with pytest.raises(
        ValueError,
        match="total_tokens must equal prompt_tokens plus completion_tokens",
    ):
        LLMProviderCallRecord(
            id=uuid4(),
            answer_id=uuid4(),
            query_trace_id=uuid4(),
            provider="fake",
            model_name="fake-llm-v1",
            status=LLMProviderCallStatus.SUCCEEDED,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=99,
            estimated_cost_usd=Decimal("0.0001"),
            latency_ms=10,
            started_at=now,
            completed_at=now,
        )


def test_llm_provider_call_record_rejects_negative_cost() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="estimated_cost_usd must not be negative"):
        LLMProviderCallRecord(
            id=uuid4(),
            answer_id=uuid4(),
            query_trace_id=uuid4(),
            provider="fake",
            model_name="fake-llm-v1",
            status=LLMProviderCallStatus.SUCCEEDED,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=Decimal("-0.01"),
            latency_ms=10,
            started_at=now,
            completed_at=now,
        )


def test_failed_llm_provider_call_requires_error_message() -> None:
    now = datetime.now(UTC)

    with pytest.raises(
        ValueError,
        match="failed provider call must include error_message",
    ):
        LLMProviderCallRecord(
            id=uuid4(),
            answer_id=None,
            query_trace_id=uuid4(),
            provider="fake",
            model_name="fake-llm-v1",
            status=LLMProviderCallStatus.FAILED,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost_usd=Decimal("0"),
            latency_ms=10,
            started_at=now,
            completed_at=now,
        )


def test_succeeded_llm_provider_call_rejects_error_message() -> None:
    now = datetime.now(UTC)

    with pytest.raises(
        ValueError,
        match="succeeded provider call must not include error_message",
    ):
        LLMProviderCallRecord(
            id=uuid4(),
            answer_id=uuid4(),
            query_trace_id=uuid4(),
            provider="fake",
            model_name="fake-llm-v1",
            status=LLMProviderCallStatus.SUCCEEDED,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=Decimal("0.0001"),
            latency_ms=10,
            started_at=now,
            completed_at=now,
            error_message="should not exist",
        )