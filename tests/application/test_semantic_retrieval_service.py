from uuid import UUID, uuid4

import pytest

from app.application.services.semantic_retrieval_service import (
    SemanticRetrievalService,
)
from app.domain.documents.entities import VectorIndexEntry
from app.domain.documents.repositories import VectorIndexEntryRepository
from app.domain.retrieval.entities import (
    QueryTrace,
    QueryTraceHit,
    RetrievedChunk,
    SemanticSearchQuery,
)
from app.domain.retrieval.enums import QueryTraceStatus
from app.domain.retrieval.repositories import (
    QueryTraceHitRepository,
    QueryTraceRepository,
)
from app.providers.fake_embedding_provider import FakeEmbeddingProvider


class InMemoryVectorIndexEntryRepository(VectorIndexEntryRepository):
    def __init__(self) -> None:
        self.results: list[RetrievedChunk] = []
        self.last_query_vector: tuple[float, ...] | None = None
        self.last_provider: str | None = None
        self.last_model_name: str | None = None
        self.last_top_k: int | None = None

    def get_by_logical_identity(
        self,
        *,
        source_document_id: UUID,
        stable_section_key: str,
        chunk_index: int,
        provider: str,
        model_name: str,
    ) -> VectorIndexEntry | None:
        return None

    def list_active_for_source_document(
        self,
        source_document_id: UUID,
    ) -> list[VectorIndexEntry]:
        return []

    def search_active_by_vector(
        self,
        *,
        query_vector: tuple[float, ...],
        provider: str,
        model_name: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        self.last_query_vector = query_vector
        self.last_provider = provider
        self.last_model_name = model_name
        self.last_top_k = top_k
        return self.results[:top_k]

    def save(self, entry: VectorIndexEntry) -> None:
        raise NotImplementedError

    def save_many(self, entries: list[VectorIndexEntry]) -> None:
        raise NotImplementedError


class InMemoryQueryTraceRepository(QueryTraceRepository):
    def __init__(self) -> None:
        self.traces: dict[UUID, QueryTrace] = {}

    def get_by_id(self, query_trace_id: UUID) -> QueryTrace | None:
        return self.traces.get(query_trace_id)

    def save(self, trace: QueryTrace) -> None:
        self.traces[trace.id] = trace


class InMemoryQueryTraceHitRepository(QueryTraceHitRepository):
    def __init__(self) -> None:
        self.hits: dict[UUID, QueryTraceHit] = {}

    def list_by_trace_id(self, query_trace_id: UUID) -> list[QueryTraceHit]:
        return sorted(
            [
                hit
                for hit in self.hits.values()
                if hit.query_trace_id == query_trace_id
            ],
            key=lambda hit: hit.rank,
        )

    def save_many(self, hits: list[QueryTraceHit]) -> None:
        for hit in hits:
            self.hits[hit.id] = hit


class InMemoryRetrievalTransaction:
    def __init__(self) -> None:
        self.vector_index_entry_repository = InMemoryVectorIndexEntryRepository()
        self.query_trace_repository = InMemoryQueryTraceRepository()
        self.query_trace_hit_repository = InMemoryQueryTraceHitRepository()

        self.vector_index_entries: VectorIndexEntryRepository = (
            self.vector_index_entry_repository
        )
        self.query_traces: QueryTraceRepository = self.query_trace_repository
        self.query_trace_hits: QueryTraceHitRepository = (
            self.query_trace_hit_repository
        )
        self.flush_count = 0
        self.commit_count = 0

    def flush(self) -> None:
        self.flush_count += 1

    def commit(self) -> None:
        self.commit_count += 1


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


def test_semantic_retrieval_service_embeds_query_and_searches_active_index() -> None:
    transaction = InMemoryRetrievalTransaction()
    transaction.vector_index_entry_repository.results = [
        make_retrieved_chunk(distance=0.05),
        make_retrieved_chunk(distance=0.25),
    ]

    service = SemanticRetrievalService(provider=FakeEmbeddingProvider())

    result = service.search(
        query=SemanticSearchQuery(
            query="What is Project Atlas status?",
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
        transaction=transaction,
    )

    assert result.query_trace_id is not None
    assert result.query == "What is Project Atlas status?"
    assert result.provider == "fake"
    assert result.model_name == "fake-embedding-v1"
    assert result.top_k == 5
    assert len(result.results) == 2
    assert result.results[0].distance == 0.05
    assert result.results[1].distance == 0.25
    assert transaction.vector_index_entry_repository.last_query_vector is not None
    assert transaction.vector_index_entry_repository.last_provider == "fake"
    assert transaction.vector_index_entry_repository.last_model_name == "fake-embedding-v1"
    assert transaction.vector_index_entry_repository.last_top_k == 5


def test_semantic_retrieval_service_persists_completed_trace_and_hits() -> None:
    transaction = InMemoryRetrievalTransaction()
    transaction.vector_index_entry_repository.results = [
        make_retrieved_chunk(distance=0.05),
        make_retrieved_chunk(distance=0.25),
    ]

    service = SemanticRetrievalService(provider=FakeEmbeddingProvider())

    result = service.search(
        query=SemanticSearchQuery(
            query="What is Project Atlas status?",
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
        transaction=transaction,
    )

    assert result.query_trace_id is not None

    trace = transaction.query_trace_repository.get_by_id(result.query_trace_id)
    assert trace is not None
    assert trace.status == QueryTraceStatus.COMPLETED
    assert trace.query == "What is Project Atlas status?"
    assert trace.provider == "fake"
    assert trace.model_name == "fake-embedding-v1"
    assert trace.results_count == 2
    assert trace.query_embedding_dimensions is not None
    assert trace.query_embedding_dimensions > 0
    assert trace.completed_at is not None
    assert trace.duration_ms is not None
    assert trace.duration_ms >= 0

    hits = transaction.query_trace_hit_repository.list_by_trace_id(
        result.query_trace_id,
    )

    assert [hit.rank for hit in hits] == [1, 2]
    assert [hit.distance for hit in hits] == [0.05, 0.25]
    assert transaction.flush_count == 1
    assert transaction.commit_count == 1


def test_semantic_retrieval_service_returns_empty_result_when_no_chunks_match() -> None:
    transaction = InMemoryRetrievalTransaction()
    service = SemanticRetrievalService(provider=FakeEmbeddingProvider())

    result = service.search(
        query=SemanticSearchQuery(
            query="What is the hiring plan?",
            top_k=3,
            provider="fake",
            model_name="fake-embedding-v1",
        ),
        transaction=transaction,
    )

    assert result.results == ()
    assert result.query_trace_id is not None

    trace = transaction.query_trace_repository.get_by_id(result.query_trace_id)

    assert trace is not None
    assert trace.status == QueryTraceStatus.COMPLETED
    assert trace.results_count == 0


def test_semantic_retrieval_service_rejects_empty_query_embedding() -> None:
    class EmptyEmbeddingProvider:
        def embed(self, text: str) -> object:
            class EmptyEmbeddingResponse:
                embedding_vector: tuple[float, ...] = ()

            return EmptyEmbeddingResponse()

    transaction = InMemoryRetrievalTransaction()

    service = SemanticRetrievalService(
        provider=EmptyEmbeddingProvider(),  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError, match="query embedding vector must not be empty"):
        service.search(
            query=SemanticSearchQuery(
                query="What is Project Atlas status?",
                top_k=5,
                provider="fake",
                model_name="fake-embedding-v1",
            ),
            transaction=transaction,
        )

    assert transaction.commit_count == 0