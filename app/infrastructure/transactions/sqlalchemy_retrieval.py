from sqlalchemy.orm import Session

from app.domain.answering.repositories import (
    AnswerCitationRecordRepository,
    AnswerRecordRepository,
)
from app.domain.documents.repositories import VectorIndexEntryRepository
from app.domain.llm_observability.repositories import (
    LLMProviderCallRecordRepository,
    LLMUsageReportRepository,
)
from app.domain.retrieval.repositories import (
    QueryTraceHitRepository,
    QueryTraceRepository,
)
from app.infrastructure.repositories import (
    SqlAlchemyAnswerCitationRecordRepository,
    SqlAlchemyAnswerRecordRepository,
    SqlAlchemyLLMProviderCallRecordRepository,
    SqlAlchemyLLMUsageReportRepository,
    SqlAlchemyQueryTraceHitRepository,
    SqlAlchemyQueryTraceRepository,
    SqlAlchemyVectorIndexEntryRepository,
)


class SqlAlchemyRetrievalTransaction:
    def __init__(self, session: Session) -> None:
        self._session = session

        self.vector_index_entries: VectorIndexEntryRepository = (
            SqlAlchemyVectorIndexEntryRepository(session)
        )
        self.query_traces: QueryTraceRepository = SqlAlchemyQueryTraceRepository(
            session,
        )
        self.query_trace_hits: QueryTraceHitRepository = (
            SqlAlchemyQueryTraceHitRepository(session)
        )

        self.answer_records: AnswerRecordRepository = SqlAlchemyAnswerRecordRepository(
            session,
        )
        self.answer_citation_records: AnswerCitationRecordRepository = (
            SqlAlchemyAnswerCitationRecordRepository(session)
        )
        self.llm_provider_calls: LLMProviderCallRecordRepository = (
            SqlAlchemyLLMProviderCallRecordRepository(session)
        )
        self.llm_usage_reports: LLMUsageReportRepository = (
            SqlAlchemyLLMUsageReportRepository(session)
        )

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()
