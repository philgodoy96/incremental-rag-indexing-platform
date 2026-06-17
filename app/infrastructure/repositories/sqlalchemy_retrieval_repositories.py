from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.domain.retrieval.entities import QueryTrace, QueryTraceHit
from app.domain.retrieval.repositories import (
    QueryTraceHitRepository,
    QueryTraceRepository,
)
from app.infrastructure.db.mappers import (
    query_trace_from_model,
    query_trace_hit_from_model,
    query_trace_hit_to_model,
    query_trace_to_model,
)
from app.infrastructure.db.models import QueryTraceHitModel, QueryTraceModel


class SqlAlchemyQueryTraceRepository(QueryTraceRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, query_trace_id: UUID) -> QueryTrace | None:
        model = self._session.get(QueryTraceModel, query_trace_id)

        if model is None:
            return None

        return query_trace_from_model(model)

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[QueryTrace]:
        statement = select(QueryTraceModel)

        if status is not None:
            statement = statement.where(QueryTraceModel.status == status)

        if provider is not None:
            statement = statement.where(QueryTraceModel.provider == provider)

        if model_name is not None:
            statement = statement.where(QueryTraceModel.model_name == model_name)

        statement = (
            statement.order_by(QueryTraceModel.started_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return [
            query_trace_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save(self, trace: QueryTrace) -> None:
        self._session.merge(query_trace_to_model(trace))


class SqlAlchemyQueryTraceHitRepository(QueryTraceHitRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_trace_id(self, query_trace_id: UUID) -> list[QueryTraceHit]:
        statement: Select[tuple[QueryTraceHitModel]] = (
            select(QueryTraceHitModel)
            .where(QueryTraceHitModel.query_trace_id == query_trace_id)
            .order_by(QueryTraceHitModel.rank)
        )

        return [
            query_trace_hit_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save_many(self, hits: list[QueryTraceHit]) -> None:
        for hit in hits:
            self._session.merge(query_trace_hit_to_model(hit))