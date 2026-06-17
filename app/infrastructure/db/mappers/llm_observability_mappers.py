from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.llm_observability.enums import LLMProviderCallStatus
from app.infrastructure.db.models import LLMProviderCallRecordModel


def llm_provider_call_record_to_model(
    entity: LLMProviderCallRecord,
) -> LLMProviderCallRecordModel:
    model = LLMProviderCallRecordModel()

    model.id = entity.id
    model.answer_id = entity.answer_id
    model.query_trace_id = entity.query_trace_id
    model.provider = entity.provider
    model.model_name = entity.model_name
    model.status = entity.status.value
    model.prompt_tokens = entity.prompt_tokens
    model.completion_tokens = entity.completion_tokens
    model.total_tokens = entity.total_tokens
    model.estimated_cost_usd = entity.estimated_cost_usd
    model.latency_ms = entity.latency_ms
    model.started_at = entity.started_at
    model.completed_at = entity.completed_at
    model.error_message = entity.error_message
    model.created_at = entity.created_at

    return model


def llm_provider_call_record_from_model(
    model: LLMProviderCallRecordModel,
) -> LLMProviderCallRecord:
    return LLMProviderCallRecord(
        id=model.id,
        answer_id=model.answer_id,
        query_trace_id=model.query_trace_id,
        provider=model.provider,
        model_name=model.model_name,
        status=LLMProviderCallStatus(model.status),
        prompt_tokens=model.prompt_tokens,
        completion_tokens=model.completion_tokens,
        total_tokens=model.total_tokens,
        estimated_cost_usd=model.estimated_cost_usd,
        latency_ms=model.latency_ms,
        started_at=model.started_at,
        completed_at=model.completed_at,
        error_message=model.error_message,
        created_at=model.created_at,
    )