from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.llm_observability.entities import LLMProviderCallRecord


class LLMProviderCallRecordRepository(ABC):
    @abstractmethod
    def get_by_id(self, provider_call_id: UUID) -> LLMProviderCallRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_answer_id(self, answer_id: UUID) -> list[LLMProviderCallRecord]:
        raise NotImplementedError

    @abstractmethod
    def save(self, record: LLMProviderCallRecord) -> None:
        raise NotImplementedError