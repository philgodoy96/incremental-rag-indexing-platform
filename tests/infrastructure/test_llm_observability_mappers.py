from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.llm_observability.enums import LLMProviderCallStatus
from app.infrastructure.db.mappers import (
    llm_provider_call_record_from_model,
    llm_provider_call_record_to_model,
)


def test_llm_provider_call_record_mapper_round_trips_succeeded_entity() -> None:
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

    model = llm_provider_call_record_to_model(record)
    mapped_record = llm_provider_call_record_from_model(model)

    assert mapped_record == record
    assert mapped_record.status == LLMProviderCallStatus.SUCCEEDED


def test_llm_provider_call_record_mapper_round_trips_failed_entity() -> None:
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

    model = llm_provider_call_record_to_model(record)
    mapped_record = llm_provider_call_record_from_model(model)

    assert mapped_record == record
    assert mapped_record.status == LLMProviderCallStatus.FAILED
    assert mapped_record.error_message == "provider timeout"