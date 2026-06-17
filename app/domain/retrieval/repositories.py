from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.retrieval.entities import QueryTrace, QueryTraceHit


class QueryTraceRepository(ABC):
    @abstractmethod
    def get_by_id(self, query_trace_id: UUID) -> QueryTrace | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, trace: QueryTrace) -> None:
        raise NotImplementedError


class QueryTraceHitRepository(ABC):
    @abstractmethod
    def list_by_trace_id(self, query_trace_id: UUID) -> list[QueryTraceHit]:
        raise NotImplementedError

    @abstractmethod
    def save_many(self, hits: list[QueryTraceHit]) -> None:
        raise NotImplementedError