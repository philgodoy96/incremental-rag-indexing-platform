from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_retrieval_transaction,
    get_semantic_retrieval_service,
)
from app.domain.retrieval.entities import (
    QueryTrace,
    QueryTraceHit,
    RetrievedChunk,
    SemanticSearchQuery,
    SemanticSearchResult,
)
from app.domain.retrieval.enums import QueryTraceStatus
from app.main import create_app


class FakeSemanticRetrievalService:
    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: object,
    ) -> SemanticSearchResult:
        return SemanticSearchResult(
            query=query.query,
            top_k=query.top_k,
            provider=query.provider,
            model_name=query.model_name,
            results=(
                RetrievedChunk(
                    vector_index_entry_id=uuid4(),
                    source_document_id=uuid4(),
                    document_version_id=uuid4(),
                    section_version_id=uuid4(),
                    chunk_version_id=uuid4(),
                    embedding_record_id=uuid4(),
                    stable_section_key="project-atlas-status/summary",
                    chunk_index=0,
                    provider=query.provider,
                    model_name=query.model_name,
                    content="Status: At Risk",
                    heading_context=("Project Atlas Status", "Summary"),
                    distance=0.12,
                ),
            ),
            query_trace_id=uuid4(),
        )


class FakeQueryTraceRepository:
    def __init__(self) -> None:
        self.trace_id = uuid4()
        started_at = datetime.now(UTC)

        self.trace = QueryTrace(
            id=self.trace_id,
            query="What is Project Atlas status?",
            provider="fake",
            model_name="fake-embedding-v1",
            top_k=5,
            started_at=started_at,
        )
        self.trace.mark_completed(
            query_embedding_dimensions=8,
            results_count=1,
            completed_at=started_at + timedelta(milliseconds=25),
        )

    def get_by_id(self, query_trace_id: UUID) -> QueryTrace | None:
        if query_trace_id != self.trace_id:
            return None

        return self.trace

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[QueryTrace]:
        traces = [self.trace]

        if status is not None:
            traces = [trace for trace in traces if trace.status.value == status]

        if provider is not None:
            traces = [trace for trace in traces if trace.provider == provider]

        if model_name is not None:
            traces = [trace for trace in traces if trace.model_name == model_name]

        return traces[offset : offset + limit]

    def save(self, trace: QueryTrace) -> None:
        self.trace = trace
        self.trace_id = trace.id


class FakeQueryTraceHitRepository:
    def __init__(self, trace_id: UUID) -> None:
        self.hit = QueryTraceHit(
            id=uuid4(),
            query_trace_id=trace_id,
            rank=1,
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
            distance=0.12,
        )

    def list_by_trace_id(self, query_trace_id: UUID) -> list[QueryTraceHit]:
        if query_trace_id != self.hit.query_trace_id:
            return []

        return [self.hit]

    def save_many(self, hits: list[QueryTraceHit]) -> None:
        if hits:
            self.hit = hits[0]


class FakeRetrievalTransaction:
    def __init__(self) -> None:
        self.query_traces = FakeQueryTraceRepository()
        self.query_trace_hits = FakeQueryTraceHitRepository(
            self.query_traces.trace_id,
        )

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        pass


def test_semantic_retrieval_search_returns_ranked_chunks() -> None:
    app = create_app()
    app.dependency_overrides[get_semantic_retrieval_service] = (
        lambda: FakeSemanticRetrievalService()
    )
    app.dependency_overrides[get_retrieval_transaction] = lambda: object()

    client = TestClient(app)

    response = client.post(
        "/api/v1/retrieval/search",
        json={
            "query": "What is the current status of Project Atlas?",
            "top_k": 5,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["query"] == "What is the current status of Project Atlas?"
    assert payload["query_trace_id"]
    assert payload["top_k"] == 5
    assert payload["provider"] == "fake"
    assert payload["model_name"] == "fake-embedding-v1"
    assert len(payload["results"]) == 1
    assert payload["results"][0]["content"] == "Status: At Risk"
    assert payload["results"][0]["heading_context"] == [
        "Project Atlas Status",
        "Summary",
    ]
    assert payload["results"][0]["distance"] == 0.12


def test_semantic_retrieval_search_validates_top_k() -> None:
    app = create_app()
    app.dependency_overrides[get_semantic_retrieval_service] = (
        lambda: FakeSemanticRetrievalService()
    )
    app.dependency_overrides[get_retrieval_transaction] = lambda: object()

    client = TestClient(app)

    response = client.post(
        "/api/v1/retrieval/search",
        json={
            "query": "What is the current status of Project Atlas?",
            "top_k": 999,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 422


def test_list_query_traces_returns_recent_traces() -> None:
    fake_transaction = FakeRetrievalTransaction()

    app = create_app()
    app.dependency_overrides[get_retrieval_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/retrieval/traces")

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == str(fake_transaction.query_traces.trace_id)
    assert payload["items"][0]["query"] == "What is Project Atlas status?"
    assert payload["items"][0]["status"] == QueryTraceStatus.COMPLETED
    assert payload["items"][0]["results_count"] == 1
    assert payload["items"][0]["duration_ms"] == 25


def test_get_query_trace_returns_trace_with_hits() -> None:
    fake_transaction = FakeRetrievalTransaction()

    app = create_app()
    app.dependency_overrides[get_retrieval_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        f"/api/v1/retrieval/traces/{fake_transaction.query_traces.trace_id}",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(fake_transaction.query_traces.trace_id)
    assert payload["query"] == "What is Project Atlas status?"
    assert payload["status"] == QueryTraceStatus.COMPLETED
    assert len(payload["hits"]) == 1
    assert payload["hits"][0]["rank"] == 1
    assert payload["hits"][0]["content"] == "Status: At Risk"
    assert payload["hits"][0]["distance"] == 0.12


def test_get_query_trace_returns_404_for_missing_trace() -> None:
    fake_transaction = FakeRetrievalTransaction()

    app = create_app()
    app.dependency_overrides[get_retrieval_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/retrieval/traces/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Query trace not found"


def test_list_query_traces_validates_limit() -> None:
    fake_transaction = FakeRetrievalTransaction()

    app = create_app()
    app.dependency_overrides[get_retrieval_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/retrieval/traces?limit=999")

    assert response.status_code == 422