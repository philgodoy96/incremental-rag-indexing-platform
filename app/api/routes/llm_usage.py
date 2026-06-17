from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_answering_transaction
from app.api.schemas.llm_usage import (
    LLMUsageByModelListResponse,
    LLMUsageSummaryResponse,
    to_llm_usage_by_model_summary_response,
    to_llm_usage_summary_response,
)
from app.application.transactions.answering import AnsweringTransaction

router = APIRouter(prefix="/llm-usage", tags=["llm-usage"])


@router.get("/summary", response_model=LLMUsageSummaryResponse)
def get_llm_usage_summary(
    transaction: Annotated[
        AnsweringTransaction,
        Depends(get_answering_transaction),
    ],
    started_at_from: datetime | None = None,
    started_at_to: datetime | None = None,
    provider: str | None = Query(default=None, min_length=1),
    model_name: str | None = Query(default=None, min_length=1),
) -> LLMUsageSummaryResponse:
    summary = transaction.llm_usage_reports.summarize(
        started_at_from=started_at_from,
        started_at_to=started_at_to,
        provider=provider,
        model_name=model_name,
    )

    return to_llm_usage_summary_response(summary)


@router.get("/by-model", response_model=LLMUsageByModelListResponse)
def get_llm_usage_by_model(
    transaction: Annotated[
        AnsweringTransaction,
        Depends(get_answering_transaction),
    ],
    started_at_from: datetime | None = None,
    started_at_to: datetime | None = None,
    provider: str | None = Query(default=None, min_length=1),
    model_name: str | None = Query(default=None, min_length=1),
) -> LLMUsageByModelListResponse:
    summaries = transaction.llm_usage_reports.summarize_by_model(
        started_at_from=started_at_from,
        started_at_to=started_at_to,
        provider=provider,
        model_name=model_name,
    )

    return LLMUsageByModelListResponse(
        items=[
            to_llm_usage_by_model_summary_response(summary)
            for summary in summaries
        ],
    )