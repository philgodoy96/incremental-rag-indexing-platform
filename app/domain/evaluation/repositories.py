from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
)


class RetrievalEvaluationCaseRepository(ABC):
    @abstractmethod
    def get_by_id(
        self,
        evaluation_case_id: UUID,
    ) -> RetrievalEvaluationCase | None:
        raise NotImplementedError

    @abstractmethod
    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        tag: str | None = None,
    ) -> list[RetrievalEvaluationCase]:
        raise NotImplementedError

    @abstractmethod
    def save(self, evaluation_case: RetrievalEvaluationCase) -> None:
        raise NotImplementedError


class RetrievalEvaluationCaseResultRepository(ABC):
    @abstractmethod
    def get_by_id(
        self,
        evaluation_case_result_id: UUID,
    ) -> RetrievalEvaluationCaseResult | None:
        raise NotImplementedError

    @abstractmethod
    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> list[RetrievalEvaluationCaseResult]:
        raise NotImplementedError

    @abstractmethod
    def list_by_case_id(
        self,
        evaluation_case_id: UUID,
    ) -> list[RetrievalEvaluationCaseResult]:
        raise NotImplementedError

    @abstractmethod
    def save(self, result: RetrievalEvaluationCaseResult) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, results: list[RetrievalEvaluationCaseResult]) -> None:
        raise NotImplementedError