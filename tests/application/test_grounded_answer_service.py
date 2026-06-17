from uuid import UUID, uuid4

import pytest

from app.application.services.grounded_answer_service import GroundedAnswerService
from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.answering.entities import GroundedAnswerRequest
from app.domain.answering.enums import GroundedAnswerStatus
from app.domain.retrieval.entities import (
    RetrievedChunk,
    SemanticSearchQuery,
    SemanticSearchResult,
)
from app.providers.fake_llm_provider import FakeLLMProvider


class FakeSemanticRetriever:
    def __init__(self, result: SemanticSearchResult) -> None:
        self.result = result
        self.last_query: SemanticSearchQuery | None = None

    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: RetrievalTransaction,
    ) -> SemanticSearchResult:
        self.last_query = query
        return self.result


class FakeTransaction:
    pass


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
        transaction=FakeTransaction(),  # type: ignore[arg-type]
    )

    assert answer.status == GroundedAnswerStatus.ANSWERED
    assert answer.query_trace_id == query_trace_id
    assert answer.answer == "Based on the retrieved context, Status: At Risk"
    assert len(answer.citations) == 1

    citation = answer.citations[0]

    assert citation.rank == 1
    assert citation.chunk_version_id == chunk.chunk_version_id
    assert citation.stable_section_key == "project-atlas-status/summary"
    assert citation.quote == "Status: At Risk"
    assert citation.distance == 0.12


def test_grounded_answer_service_passes_request_to_semantic_retriever() -> None:
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
        transaction=FakeTransaction(),  # type: ignore[arg-type]
    )

    assert retriever.last_query is not None
    assert retriever.last_query.query == "What is Project Atlas status?"
    assert retriever.last_query.top_k == 3
    assert retriever.last_query.provider == "fake"
    assert retriever.last_query.model_name == "fake-embedding-v1"


def test_grounded_answer_service_returns_insufficient_context_when_no_chunks_found() -> None:
    query_trace_id = uuid4()

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
        transaction=FakeTransaction(),  # type: ignore[arg-type]
    )

    assert answer.status == GroundedAnswerStatus.INSUFFICIENT_CONTEXT
    assert answer.query_trace_id == query_trace_id
    assert answer.citations == ()
    assert "not have enough retrieved context" in answer.answer


def test_grounded_answer_service_requires_query_trace_id() -> None:
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
            transaction=FakeTransaction(),  # type: ignore[arg-type]
        )