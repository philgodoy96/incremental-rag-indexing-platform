from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_answering_transaction
from app.api.schemas.llm_provider_calls import (
    LLMProviderCallListResponse,
    LLMProviderCallResponse,
    to_llm_provider_call_response,
)
from app.application.transactions.answering import AnsweringTransaction
from app.domain.llm_observability.enums import LLMProviderCallStatus

router = APIRouter(prefix="/llm-provider-calls", tags=["llm-provider-calls"])


@router.get("", response_model=LLMProviderCallListResponse)
def list_llm_provider_calls(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: LLMProviderCallStatus | None = None,
    provider: str | None = Query(default=None, min_length=1),
    model_name: str | None = Query(default=None, min_length=1),
    transaction: AnsweringTransaction = Depends(get_answering_transaction),
) -> LLMProviderCallListResponse:
    records = transaction.llm_provider_calls.list_recent(
        limit=limit,
        offset=offset,
        status=status.value if status is not None else None,
        provider=provider,
        model_name=model_name,
    )

    return LLMProviderCallListResponse(
        items=[to_llm_provider_call_response(record) for record in records],
        limit=limit,
        offset=offset,
    )


@router.get("/{provider_call_id}", response_model=LLMProviderCallResponse)
def get_llm_provider_call(
    provider_call_id: UUID,
    transaction: AnsweringTransaction = Depends(get_answering_transaction),
) -> LLMProviderCallResponse:
    record = transaction.llm_provider_calls.get_by_id(provider_call_id)

    if record is None:
        raise HTTPException(status_code=404, detail="LLM provider call not found")

    return to_llm_provider_call_response(record)
