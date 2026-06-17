from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_retrieval_transaction,
    get_semantic_retrieval_service,
)
from app.domain.retrieval.entities import (
    RetrievedChunk,
    SemanticSearchQuery,
    SemanticSearchResult,
)
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
        )


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