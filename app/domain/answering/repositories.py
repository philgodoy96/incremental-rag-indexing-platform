from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.answering.entities import AnswerCitationRecord, AnswerRecord


class AnswerRecordRepository(ABC):
    @abstractmethod
    def get_by_id(self, answer_id: UUID) -> AnswerRecord | None:
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
    ) -> list[AnswerRecord]:
        raise NotImplementedError

    @abstractmethod
    def save(self, answer: AnswerRecord) -> None:
        raise NotImplementedError


class AnswerCitationRecordRepository(ABC):
    @abstractmethod
    def list_by_answer_id(self, answer_id: UUID) -> list[AnswerCitationRecord]:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, citations: list[AnswerCitationRecord]) -> None:
        raise NotImplementedError