from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.llm_observability.enums import LLMProviderCallStatus
from app.domain.llm_observability.repositories import (
    LLMProviderCallRecordRepository,
    LLMUsageReportRepository,
)
from app.domain.llm_observability.usage_reports import (
    LLMUsageByModelSummary,
    LLMUsageSummary,
)
from app.infrastructure.db.mappers import (
    llm_provider_call_record_from_model,
    llm_provider_call_record_to_model,
)
from app.infrastructure.db.models import LLMProviderCallRecordModel


def _to_int(value: object) -> int:
    if value is None:
        return 0

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, Decimal):
        return int(value)

    return int(str(value))


def _to_float(value: object) -> float:
    if value is None:
        return 0.0

    if isinstance(value, float):
        return value

    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)

    if isinstance(value, Decimal):
        return float(value)

    return float(str(value))


def _to_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0")

    if isinstance(value, Decimal):
        return value

    return Decimal(str(value))


class SqlAlchemyLLMProviderCallRecordRepository(LLMProviderCallRecordRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, provider_call_id: UUID) -> LLMProviderCallRecord | None:
        model = self._session.get(LLMProviderCallRecordModel, provider_call_id)

        if model is None:
            return None

        return llm_provider_call_record_from_model(model)

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMProviderCallRecord]:
        statement = select(LLMProviderCallRecordModel)

        if status is not None:
            statement = statement.where(LLMProviderCallRecordModel.status == status)

        if provider is not None:
            statement = statement.where(LLMProviderCallRecordModel.provider == provider)

        if model_name is not None:
            statement = statement.where(
                LLMProviderCallRecordModel.model_name == model_name,
            )

        statement = (
            statement.order_by(LLMProviderCallRecordModel.started_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return [
            llm_provider_call_record_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def list_by_answer_id(self, answer_id: UUID) -> list[LLMProviderCallRecord]:
        statement = (
            select(LLMProviderCallRecordModel)
            .where(LLMProviderCallRecordModel.answer_id == answer_id)
            .order_by(LLMProviderCallRecordModel.started_at)
        )

        return [
            llm_provider_call_record_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save(self, record: LLMProviderCallRecord) -> None:
        self._session.merge(llm_provider_call_record_to_model(record))


class SqlAlchemyLLMUsageReportRepository(LLMUsageReportRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def summarize(
        self,
        *,
        started_at_from: datetime | None = None,
        started_at_to: datetime | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> LLMUsageSummary:
        statement = select(
            func.count(LLMProviderCallRecordModel.id).label("call_count"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            LLMProviderCallRecordModel.status
                            == LLMProviderCallStatus.SUCCEEDED.value,
                            1,
                        ),
                        else_=0,
                    ),
                ),
                0,
            ).label("succeeded_count"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            LLMProviderCallRecordModel.status
                            == LLMProviderCallStatus.FAILED.value,
                            1,
                        ),
                        else_=0,
                    ),
                ),
                0,
            ).label("failed_count"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.prompt_tokens),
                0,
            ).label("prompt_tokens"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.completion_tokens),
                0,
            ).label("completion_tokens"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.total_tokens),
                0,
            ).label("total_tokens"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.estimated_cost_usd),
                Decimal("0"),
            ).label("estimated_cost_usd"),
            func.coalesce(
                func.avg(LLMProviderCallRecordModel.latency_ms),
                0,
            ).label("average_latency_ms"),
        )

        if started_at_from is not None:
            statement = statement.where(
                LLMProviderCallRecordModel.started_at >= started_at_from,
            )

        if started_at_to is not None:
            statement = statement.where(
                LLMProviderCallRecordModel.started_at < started_at_to,
            )

        if provider is not None:
            statement = statement.where(LLMProviderCallRecordModel.provider == provider)

        if model_name is not None:
            statement = statement.where(
                LLMProviderCallRecordModel.model_name == model_name,
            )

        row = self._session.execute(statement).one()

        return LLMUsageSummary(
            call_count=_to_int(row.call_count),
            succeeded_count=_to_int(row.succeeded_count),
            failed_count=_to_int(row.failed_count),
            prompt_tokens=_to_int(row.prompt_tokens),
            completion_tokens=_to_int(row.completion_tokens),
            total_tokens=_to_int(row.total_tokens),
            estimated_cost_usd=_to_decimal(row.estimated_cost_usd),
            average_latency_ms=_to_float(row.average_latency_ms),
        )

    def summarize_by_model(
        self,
        *,
        started_at_from: datetime | None = None,
        started_at_to: datetime | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMUsageByModelSummary]:
        statement = select(
            LLMProviderCallRecordModel.provider.label("provider"),
            LLMProviderCallRecordModel.model_name.label("model_name"),
            func.count(LLMProviderCallRecordModel.id).label("call_count"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            LLMProviderCallRecordModel.status
                            == LLMProviderCallStatus.SUCCEEDED.value,
                            1,
                        ),
                        else_=0,
                    ),
                ),
                0,
            ).label("succeeded_count"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            LLMProviderCallRecordModel.status
                            == LLMProviderCallStatus.FAILED.value,
                            1,
                        ),
                        else_=0,
                    ),
                ),
                0,
            ).label("failed_count"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.prompt_tokens),
                0,
            ).label("prompt_tokens"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.completion_tokens),
                0,
            ).label("completion_tokens"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.total_tokens),
                0,
            ).label("total_tokens"),
            func.coalesce(
                func.sum(LLMProviderCallRecordModel.estimated_cost_usd),
                Decimal("0"),
            ).label("estimated_cost_usd"),
            func.coalesce(
                func.avg(LLMProviderCallRecordModel.latency_ms),
                0,
            ).label("average_latency_ms"),
        )

        if started_at_from is not None:
            statement = statement.where(
                LLMProviderCallRecordModel.started_at >= started_at_from,
            )

        if started_at_to is not None:
            statement = statement.where(
                LLMProviderCallRecordModel.started_at < started_at_to,
            )

        if provider is not None:
            statement = statement.where(LLMProviderCallRecordModel.provider == provider)

        if model_name is not None:
            statement = statement.where(
                LLMProviderCallRecordModel.model_name == model_name,
            )

        statement = (
            statement.group_by(
                LLMProviderCallRecordModel.provider,
                LLMProviderCallRecordModel.model_name,
            )
            .order_by(
                LLMProviderCallRecordModel.provider,
                LLMProviderCallRecordModel.model_name,
            )
        )

        return [
            LLMUsageByModelSummary(
                provider=row.provider,
                model_name=row.model_name,
                call_count=_to_int(row.call_count),
                succeeded_count=_to_int(row.succeeded_count),
                failed_count=_to_int(row.failed_count),
                prompt_tokens=_to_int(row.prompt_tokens),
                completion_tokens=_to_int(row.completion_tokens),
                total_tokens=_to_int(row.total_tokens),
                estimated_cost_usd=_to_decimal(row.estimated_cost_usd),
                average_latency_ms=_to_float(row.average_latency_ms),
            )
            for row in self._session.execute(statement).all()
        ]