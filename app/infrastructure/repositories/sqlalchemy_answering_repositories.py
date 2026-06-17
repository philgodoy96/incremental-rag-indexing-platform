from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.domain.answering.entities import AnswerCitationRecord, AnswerRecord
from app.domain.answering.repositories import (
    AnswerCitationRecordRepository,
    AnswerRecordRepository,
)
from app.infrastructure.db.mappers import (
    answer_citation_record_from_model,
    answer_citation_record_to_model,
    answer_record_from_model,
    answer_record_to_model,
)
from app.infrastructure.db.models import (
    AnswerCitationRecordModel,
    AnswerRecordModel,
)


class SqlAlchemyAnswerRecordRepository(AnswerRecordRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, answer_id: UUID) -> AnswerRecord | None:
        model = self._session.get(AnswerRecordModel, answer_id)

        if model is None:
            return None

        return answer_record_from_model(model)

    def save(self, answer: AnswerRecord) -> None:
        self._session.merge(answer_record_to_model(answer))


class SqlAlchemyAnswerCitationRecordRepository(AnswerCitationRecordRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_answer_id(self, answer_id: UUID) -> list[AnswerCitationRecord]:
        statement: Select[tuple[AnswerCitationRecordModel]] = (
            select(AnswerCitationRecordModel)
            .where(AnswerCitationRecordModel.answer_id == answer_id)
            .order_by(AnswerCitationRecordModel.rank)
        )

        return [
            answer_citation_record_from_model(model)
            for model in self._session.execute(statement).scalars().all()
        ]

    def save_many(self, citations: list[AnswerCitationRecord]) -> None:
        for citation in citations:
            self._session.merge(answer_citation_record_to_model(citation))