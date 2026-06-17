from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
)
from app.domain.evaluation.repositories import (
    RetrievalEvaluationCaseRepository,
    RetrievalEvaluationCaseResultRepository,
)
from app.infrastructure.db.mappers import (
    retrieval_evaluation_case_from_model,
    retrieval_evaluation_case_result_from_model,
    retrieval_evaluation_case_result_to_model,
    retrieval_evaluation_case_to_model,
)
from app.infrastructure.db.models import (
    RetrievalEvaluationCaseModel,
    RetrievalEvaluationCaseResultModel,
)


class SqlAlchemyRetrievalEvaluationCaseRepository(
    RetrievalEvaluationCaseRepository,
):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(
        self,
        evaluation_case_id: UUID,
    ) -> RetrievalEvaluationCase | None:
        model = self._session.get(RetrievalEvaluationCaseModel, evaluation_case_id)

        if model is None:
            return None

        return retrieval_evaluation_case_from_model(model)

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        tag: str | None = None,
    ) -> list[RetrievalEvaluationCase]:
        statement = select(RetrievalEvaluationCaseModel)

        if tag is not None:
            statement = statement.where(
                RetrievalEvaluationCaseModel.tags.contains([tag]),
            )

        statement = (
            statement.order_by(RetrievalEvaluationCaseModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return [
            retrieval_evaluation_case_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save(self, evaluation_case: RetrievalEvaluationCase) -> None:
        self._session.merge(retrieval_evaluation_case_to_model(evaluation_case))


class SqlAlchemyRetrievalEvaluationCaseResultRepository(
    RetrievalEvaluationCaseResultRepository,
):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(
        self,
        evaluation_case_result_id: UUID,
    ) -> RetrievalEvaluationCaseResult | None:
        model = self._session.get(
            RetrievalEvaluationCaseResultModel,
            evaluation_case_result_id,
        )

        if model is None:
            return None

        return retrieval_evaluation_case_result_from_model(model)

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> list[RetrievalEvaluationCaseResult]:
        statement = select(RetrievalEvaluationCaseResultModel)

        if status is not None:
            statement = statement.where(
                RetrievalEvaluationCaseResultModel.status == status,
            )

        statement = (
            statement.order_by(RetrievalEvaluationCaseResultModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return [
            retrieval_evaluation_case_result_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def list_by_case_id(
        self,
        evaluation_case_id: UUID,
    ) -> list[RetrievalEvaluationCaseResult]:
        statement = (
            select(RetrievalEvaluationCaseResultModel)
            .where(
                RetrievalEvaluationCaseResultModel.evaluation_case_id
                == evaluation_case_id,
            )
            .order_by(RetrievalEvaluationCaseResultModel.created_at.desc())
        )

        return [
            retrieval_evaluation_case_result_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save(self, result: RetrievalEvaluationCaseResult) -> None:
        self._session.merge(retrieval_evaluation_case_result_to_model(result))

    def save_many(self, results: list[RetrievalEvaluationCaseResult]) -> None:
        for result in results:
            self.save(result)