from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.llm_observability.repositories import (
    LLMProviderCallRecordRepository,
)
from app.infrastructure.db.mappers import (
    llm_provider_call_record_from_model,
    llm_provider_call_record_to_model,
)
from app.infrastructure.db.models import LLMProviderCallRecordModel


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
        statement: Select[tuple[LLMProviderCallRecordModel]] = (
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