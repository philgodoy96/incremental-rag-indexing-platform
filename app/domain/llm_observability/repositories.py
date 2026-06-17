from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.llm_observability.usage_reports import (
    LLMUsageByModelSummary,
    LLMUsageSummary,
)


class LLMProviderCallRecordRepository(ABC):
    @abstractmethod
    def get_by_id(self, provider_call_id: UUID) -> LLMProviderCallRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMProviderCallRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_by_answer_id(self, answer_id: UUID) -> list[LLMProviderCallRecord]:
        raise NotImplementedError

    @abstractmethod
    def save(self, record: LLMProviderCallRecord) -> None:
        raise NotImplementedError


class LLMUsageReportRepository(ABC):
    @abstractmethod
    def summarize(
        self,
        *,
        started_at_from: datetime | None = None,
        started_at_to: datetime | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> LLMUsageSummary:
        raise NotImplementedError

    @abstractmethod
    def summarize_by_model(
        self,
        *,
        started_at_from: datetime | None = None,
        started_at_to: datetime | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMUsageByModelSummary]:
        raise NotImplementedError
