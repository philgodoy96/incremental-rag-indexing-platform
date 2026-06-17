from uuid import UUID, uuid4

import pytest

from app.application.services.semantic_retrieval_service import (
    SemanticRetrievalService,
)
from app.domain.documents.entities import VectorIndexEntry
from app.domain.documents.repositories import VectorIndexEntryRepository
from app.domain.retrieval.entities import RetrievedChunk, SemanticSearchQuery
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


class InMemoryRetrievalTransaction:
    def __init__(self) -> None:
        self.vector_index_entry_repository = InMemoryVectorIndexEntryRepository()
        self.vector_index_entries: VectorIndexEntryRepository = (
            self.vector_index_entry_repository
        )


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