from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.application.services.grounded_answer_service import GroundedAnswerService
from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.answering.entities import (
    AnswerCitationRecord,
    AnswerRecord,
    GroundedAnswerRequest,
)
from app.domain.answering.enums import GroundedAnswerStatus
from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.retrieval.entities import (
    RetrievedChunk,
    SemanticSearchQuery,
    SemanticSearchResult,
)
from app.providers.fake_llm_provider import FakeLLMProvider
from app.providers.llm import (
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMProviderError,
)


class FakeSemanticRetriever:
    def __init__(self, result: SemanticSearchResult) -> None:
        self.result = result
        self.last_query: SemanticSearchQuery | None = None
        self.query_trace_id = result.query_trace_id

    @classmethod
    def with_results(cls) -> "FakeSemanticRetriever":
        return cls(make_search_result(results=(make_retrieved_chunk(),)))

    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: RetrievalTransaction,
    ) -> SemanticSearchResult:
        self.last_query = query
        return self.result


class InMemoryAnswerRecordRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, AnswerRecord] = {}
        self._save_order: list[UUID] = []

    def get_by_id(self, answer_id: UUID) -> AnswerRecord | None:
        return self.records.get(answer_id)

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[AnswerRecord]:
        records = list(self.records.values())
        save_order = {
            answer_id: index for index, answer_id in enumerate(self._save_order)
        }

        if status is not None:
            records = [record for record in records if record.status.value == status]

        if provider is not None:
            records = [record for record in records if record.provider == provider]

        if model_name is not None:
            records = [record for record in records if record.model_name == model_name]

        records = sorted(
            records,
            key=lambda record: (record.created_at, save_order[record.id]),
            reverse=True,
        )

        return records[offset : offset + limit]

    def save(self, answer: AnswerRecord) -> None:
        self.records[answer.id] = answer
        if answer.id not in self._save_order:
            self._save_order.append(answer.id)


class InMemoryAnswerCitationRecordRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, AnswerCitationRecord] = {}

    def list_by_answer_id(self, answer_id: UUID) -> list[AnswerCitationRecord]:
        return sorted(
            [
                record
                for record in self.records.values()
                if record.answer_id == answer_id
            ],
            key=lambda record: record.rank,
        )

    def save_many(self, citations: list[AnswerCitationRecord]) -> None:
        for citation in citations:
            self.records[citation.id] = citation


class InMemoryLLMProviderCallRecordRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, LLMProviderCallRecord] = {}

    def get_by_id(
        self,
        provider_call_id: UUID,
    ) -> LLMProviderCallRecord | None:
        return self.records.get(provider_call_id)

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMProviderCallRecord]:
        records = list(self.records.values())

        if status is not None:
            records = [record for record in records if record.status.value == status]

        if provider is not None:
            records = [record for record in records if record.provider == provider]

        if model_name is not None:
            records = [record for record in records if record.model_name == model_name]

        records = sorted(records, key=lambda record: record.started_at, reverse=True)

        return records[offset : offset + limit]

    def list_by_answer_id(
        self,
        answer_id: UUID,
    ) -> list[LLMProviderCallRecord]:
        return sorted(
            [
                record
                for record in self.records.values()
                if record.answer_id == answer_id
            ],
            key=lambda record: record.started_at,
        )

    def save(self, record: LLMProviderCallRecord) -> None:
        self.records[record.id] = record


class FakeTransaction:
    def __init__(self) -> None:
        self.answer_records = InMemoryAnswerRecordRepository()
        self.answer_citation_records = InMemoryAnswerCitationRecordRepository()
        self.llm_provider_calls = InMemoryLLMProviderCallRecordRepository()
        self.flush_count = 0
        self.commit_count = 0

    def flush(self) -> None:
        self.flush_count += 1

    def commit(self) -> None:
        self.commit_count += 1


class FailingLLMProvider:
    @property
    def provider(self) -> str:
        return "fake"

    @property
    def model_name(self) -> str:
        return "fake-llm-v1"

    def generate_answer(
        self,
        request: LLMGenerationRequest,
    ) -> LLMGenerationResponse:
        raise LLMProviderError("provider timeout")


class UnexpectedFailingLLMProvider:
    @property
    def provider(self) -> str:
        return "fake"

    @property
    def model_name(self) -> str:
        return "fake-llm-v1"

    def generate_answer(
        self,
        request: LLMGenerationRequest,
    ) -> LLMGenerationResponse:
        raise RuntimeError("socket closed")


def make_retrieved_chunk(distance: float = 0.12) -> RetrievedChunk:
    return RetrievedChunk(
        vector_index_entry_id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        chunk_index=0,
        provider="fake",
        model_name="fake-embedding-v1",
        content="Status: At Risk",
        heading_context=("Project Atlas Status", "Summary"),
        distance=distance,
    )


def make_search_result(
    *,
    results: tuple[RetrievedChunk, ...],
    query_trace_id: UUID | None = None,
    use_missing_query_trace_id: bool = False,
) -> SemanticSearchResult:
    return SemanticSearchResult(
        query="What is Project Atlas status?",
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
        results=results,
        query_trace_id=None if use_missing_query_trace_id else query_trace_id or uuid4(),
    )


def test_grounded_answer_service_generates_answer_with_citations() -> None:
    chunk = make_retrieved_chunk(distance=0.12)
    query_trace_id = uuid4()
    transaction = FakeTransaction()

    retriever = FakeSemanticRetriever(
        make_search_result(
            results=(chunk,),
            query_trace_id=query_trace_id,
        ),
    )

    service = GroundedAnswerService(
        retriever=retriever,
        llm_provider=FakeLLMProvider(),
    )

    answer = service.answer(
        request=GroundedAnswerRequest(
            question="What is Project Atlas status?",
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert answer.status == GroundedAnswerStatus.ANSWERED
    assert answer.query_trace_id == query_trace_id
    assert answer.answer_id is not None
    assert answer.answer == "Based on the retrieved context, Status: At Risk"
    assert len(answer.citations) == 1

    citation = answer.citations[0]

    assert citation.rank == 1
    assert citation.chunk_version_id == chunk.chunk_version_id
    assert citation.stable_section_key == "project-atlas-status/summary"
    assert citation.quote == "Status: At Risk"
    assert citation.distance == 0.12


def test_grounded_answer_service_persists_answer_record_and_citations() -> None:
    chunk = make_retrieved_chunk(distance=0.12)
    transaction = FakeTransaction()

    retriever = FakeSemanticRetriever(
        make_search_result(results=(chunk,)),
    )

    service = GroundedAnswerService(
        retriever=retriever,
        llm_provider=FakeLLMProvider(),
    )

    answer = service.answer(
        request=GroundedAnswerRequest(
            question="What is Project Atlas status?",
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert answer.answer_id is not None

    answer_record = transaction.answer_records.get_by_id(answer.answer_id)

    assert answer_record is not None
    assert answer_record.question == "What is Project Atlas status?"
    assert answer_record.answer == "Based on the retrieved context, Status: At Risk"
    assert answer_record.status == GroundedAnswerStatus.ANSWERED
    assert answer_record.query_trace_id == answer.query_trace_id
    assert answer_record.top_k == 5
    assert answer_record.provider == "fake"
    assert answer_record.model_name == "fake-embedding-v1"

    citation_records = transaction.answer_citation_records.list_by_answer_id(
        answer.answer_id,
    )

    assert len(citation_records) == 1
    assert citation_records[0].rank == 1
    assert citation_records[0].chunk_version_id == chunk.chunk_version_id
    assert citation_records[0].quote == "Status: At Risk"
    assert citation_records[0].distance == 0.12

    provider_calls = transaction.llm_provider_calls.list_by_answer_id(
        answer.answer_id,
    )

    assert len(provider_calls) == 1

    provider_call = provider_calls[0]

    assert provider_call.answer_id == answer.answer_id
    assert provider_call.query_trace_id == answer.query_trace_id
    assert provider_call.provider == "fake"
    assert provider_call.model_name == "fake-llm-v1"
    assert provider_call.prompt_tokens > 0
    assert provider_call.completion_tokens > 0
    assert provider_call.total_tokens == (
        provider_call.prompt_tokens + provider_call.completion_tokens
    )
    assert provider_call.estimated_cost_usd == Decimal("0")
    assert provider_call.latency_ms >= 0
    assert provider_call.error_message is None

    assert transaction.flush_count == 1
    assert transaction.commit_count == 1


def test_grounded_answer_service_passes_request_to_semantic_retriever() -> None:
    transaction = FakeTransaction()
    retriever = FakeSemanticRetriever(
        make_search_result(results=(make_retrieved_chunk(),)),
    )

    service = GroundedAnswerService(
        retriever=retriever,
        llm_provider=FakeLLMProvider(),
    )

    service.answer(
        request=GroundedAnswerRequest(
            question="What is Project Atlas status?",
            top_k=3,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert retriever.last_query is not None
    assert retriever.last_query.query == "What is Project Atlas status?"
    assert retriever.last_query.top_k == 3
    assert retriever.last_query.provider == "fake"
    assert retriever.last_query.model_name == "fake-embedding-v1"


def test_grounded_answer_service_persists_insufficient_context_answer() -> None:
    query_trace_id = uuid4()
    transaction = FakeTransaction()

    retriever = FakeSemanticRetriever(
        make_search_result(
            results=(),
            query_trace_id=query_trace_id,
        ),
    )

    service = GroundedAnswerService(
        retriever=retriever,
        llm_provider=FakeLLMProvider(),
    )

    answer = service.answer(
        request=GroundedAnswerRequest(
            question="What is Project Phoenix budget?",
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
        transaction=transaction,  # type: ignore[arg-type]
    )

    assert answer.status == GroundedAnswerStatus.INSUFFICIENT_CONTEXT
    assert answer.query_trace_id == query_trace_id
    assert answer.answer_id is not None
    assert answer.citations == ()

    answer_record = transaction.answer_records.get_by_id(answer.answer_id)

    assert answer_record is not None
    assert answer_record.status == GroundedAnswerStatus.INSUFFICIENT_CONTEXT
    assert answer_record.answer == answer.answer

    citation_records = transaction.answer_citation_records.list_by_answer_id(
        answer.answer_id,
    )

    assert citation_records == []

    provider_calls = transaction.llm_provider_calls.list_by_answer_id(
        answer.answer_id,
    )

    assert provider_calls == []

    assert transaction.flush_count == 1
    assert transaction.commit_count == 1


def test_grounded_answer_service_requires_query_trace_id() -> None:
    transaction = FakeTransaction()

    retriever = FakeSemanticRetriever(
        make_search_result(
            results=(make_retrieved_chunk(),),
            use_missing_query_trace_id=True,
        ),
    )

    service = GroundedAnswerService(
        retriever=retriever,
        llm_provider=FakeLLMProvider(),
    )

    with pytest.raises(RuntimeError, match="query trace id is required"):
        service.answer(
            request=GroundedAnswerRequest(
                question="What is Project Atlas status?",
                top_k=5,
                provider="fake",
                model_name="fake-embedding-v1",
            ),
            transaction=transaction,  # type: ignore[arg-type]
        )

    assert transaction.flush_count == 0
    assert transaction.commit_count == 0


def test_in_memory_answer_record_repository_lists_recent_records() -> None:
    repository = InMemoryAnswerRecordRepository()

    first = AnswerRecord(
        id=uuid4(),
        question="First question",
        answer="First answer",
        status=GroundedAnswerStatus.ANSWERED,
        query_trace_id=uuid4(),
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
    )
    second = AnswerRecord(
        id=uuid4(),
        question="Second question",
        answer="Second answer",
        status=GroundedAnswerStatus.ANSWERED,
        query_trace_id=uuid4(),
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
    )

    repository.save(first)
    repository.save(second)

    records = repository.list_recent(limit=10, offset=0)

    assert [record.id for record in records] == [second.id, first.id]


def test_in_memory_llm_provider_call_repository_lists_recent_records() -> None:
    repository = InMemoryLLMProviderCallRecordRepository()

    first_started_at = datetime.now(UTC)
    second_started_at = first_started_at + timedelta(milliseconds=10)

    first = LLMProviderCallRecord.succeeded(
        answer_id=uuid4(),
        query_trace_id=uuid4(),
        provider="fake",
        model_name="fake-llm-v1",
        prompt_tokens=10,
        completion_tokens=5,
        estimated_cost_usd=Decimal("0"),
        started_at=first_started_at,
        completed_at=first_started_at + timedelta(milliseconds=1),
    )
    second = LLMProviderCallRecord.succeeded(
        answer_id=uuid4(),
        query_trace_id=uuid4(),
        provider="fake",
        model_name="fake-llm-v1",
        prompt_tokens=12,
        completion_tokens=6,
        estimated_cost_usd=Decimal("0"),
        started_at=second_started_at,
        completed_at=second_started_at + timedelta(milliseconds=1),
    )

    repository.save(first)
    repository.save(second)

    records = repository.list_recent(limit=10, offset=0)

    assert [record.id for record in records] == [second.id, first.id]


def test_grounded_answer_service_persists_failed_llm_provider_call() -> None:
    retriever = FakeSemanticRetriever.with_results()
    llm_provider = FailingLLMProvider()
    transaction = FakeTransaction()
    service = GroundedAnswerService(
        retriever=retriever,
        llm_provider=llm_provider,
    )

    with pytest.raises(LLMProviderError, match="provider timeout"):
        service.answer(
            request=GroundedAnswerRequest(
                question="What is Project Atlas status?",
                top_k=5,
                provider="fake",
                model_name="fake-embedding-v1",
            ),
            transaction=transaction,  # type: ignore[arg-type]
        )

    provider_calls = transaction.llm_provider_calls.list_recent(
        limit=10,
        offset=0,
        status="failed",
    )

    assert len(provider_calls) == 1

    provider_call = provider_calls[0]

    assert provider_call.answer_id is None
    assert provider_call.query_trace_id == retriever.query_trace_id
    assert provider_call.provider == "fake"
    assert provider_call.model_name == "fake-llm-v1"
    assert provider_call.status.value == "failed"
    assert provider_call.prompt_tokens == 0
    assert provider_call.completion_tokens == 0
    assert provider_call.total_tokens == 0
    assert provider_call.estimated_cost_usd == Decimal("0")
    assert provider_call.latency_ms >= 0
    assert provider_call.error_message == "provider timeout"
    assert transaction.commit_count == 1


def test_grounded_answer_service_persists_unexpected_llm_provider_error() -> None:
    retriever = FakeSemanticRetriever.with_results()
    llm_provider = UnexpectedFailingLLMProvider()
    transaction = FakeTransaction()
    service = GroundedAnswerService(
        retriever=retriever,
        llm_provider=llm_provider,
    )

    with pytest.raises(LLMProviderError, match="unexpected LLM provider error"):
        service.answer(
            request=GroundedAnswerRequest(
                question="What is Project Atlas status?",
                top_k=5,
                provider="fake",
                model_name="fake-embedding-v1",
            ),
            transaction=transaction,  # type: ignore[arg-type]
        )

    provider_calls = transaction.llm_provider_calls.list_recent(
        limit=10,
        offset=0,
        status="failed",
    )

    assert len(provider_calls) == 1

    provider_call = provider_calls[0]

    assert provider_call.answer_id is None
    assert provider_call.query_trace_id == retriever.query_trace_id
    assert provider_call.provider == "fake"
    assert provider_call.model_name == "fake-llm-v1"
    assert provider_call.status.value == "failed"
    assert provider_call.prompt_tokens == 0
    assert provider_call.completion_tokens == 0
    assert provider_call.total_tokens == 0
    assert provider_call.estimated_cost_usd == Decimal("0")
    assert provider_call.latency_ms >= 0
    assert provider_call.error_message == (
        "unexpected provider error: RuntimeError: socket closed"
    )
    assert transaction.commit_count == 1
