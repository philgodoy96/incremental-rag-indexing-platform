from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_answering_transaction,
    get_semantic_retrieval_service,
)
from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
)
from app.domain.retrieval.entities import SemanticSearchQuery
from app.main import create_app


@dataclass(frozen=True, slots=True)
class FakeRetrievedChunk:
    chunk_version_id: UUID


@dataclass(frozen=True, slots=True)
class FakeSemanticSearchResult:
    results: tuple[FakeRetrievedChunk, ...]


class FakeSemanticRetriever:
    def __init__(self, retrieved_chunk_version_ids: tuple[UUID, ...]) -> None:
        self.retrieved_chunk_version_ids = retrieved_chunk_version_ids
        self.queries: list[SemanticSearchQuery] = []

    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: object,
    ) -> FakeSemanticSearchResult:
        self.queries.append(query)

        return FakeSemanticSearchResult(
            results=tuple(
                FakeRetrievedChunk(chunk_version_id=chunk_version_id)
                for chunk_version_id in self.retrieved_chunk_version_ids
            ),
        )


class FakeRetrievalEvaluationCaseRepository:
    def __init__(self) -> None:
        self.expected_chunk_id = uuid4()
        self.evaluation_case = RetrievalEvaluationCase.create(
            name="Project Atlas status",
            query="What is Project Atlas status?",
            expected_chunk_version_ids=(self.expected_chunk_id,),
            tags=("status", "project-atlas"),
        )

    def get_by_id(
        self,
        evaluation_case_id: UUID,
    ) -> RetrievalEvaluationCase | None:
        if evaluation_case_id != self.evaluation_case.id:
            return None

        return self.evaluation_case

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        tag: str | None = None,
    ) -> list[RetrievalEvaluationCase]:
        evaluation_cases = [self.evaluation_case]

        if tag is not None:
            evaluation_cases = [
                evaluation_case
                for evaluation_case in evaluation_cases
                if tag in evaluation_case.tags
            ]

        return evaluation_cases[offset : offset + limit]

    def save(self, evaluation_case: RetrievalEvaluationCase) -> None:
        self.evaluation_case = evaluation_case


class FakeRetrievalEvaluationCaseResultRepository:
    def __init__(self) -> None:
        self.results: list[RetrievalEvaluationCaseResult] = []

    def get_by_id(
        self,
        evaluation_case_result_id: UUID,
    ) -> RetrievalEvaluationCaseResult | None:
        for result in self.results:
            if result.id == evaluation_case_result_id:
                return result

        return None

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> list[RetrievalEvaluationCaseResult]:
        results = list(self.results)

        if status is not None:
            results = [result for result in results if result.status.value == status]

        return results[offset : offset + limit]

    def list_by_case_id(
        self,
        evaluation_case_id: UUID,
    ) -> list[RetrievalEvaluationCaseResult]:
        return [
            result
            for result in self.results
            if result.evaluation_case_id == evaluation_case_id
        ]

    def save(self, result: RetrievalEvaluationCaseResult) -> None:
        self.results.append(result)

    def save_many(self, results: list[RetrievalEvaluationCaseResult]) -> None:
        self.results.extend(results)


class FakeTransaction:
    def __init__(self) -> None:
        self.retrieval_evaluation_cases = FakeRetrievalEvaluationCaseRepository()
        self.retrieval_evaluation_case_results = (
            FakeRetrievalEvaluationCaseResultRepository()
        )
        self.commit_count = 0

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.commit_count += 1


def test_run_retrieval_evaluation_returns_results_and_summary() -> None:
    fake_transaction = FakeTransaction()
    fake_retriever = FakeSemanticRetriever(
        retrieved_chunk_version_ids=(
            fake_transaction.retrieval_evaluation_cases.expected_chunk_id,
        ),
    )

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction
    app.dependency_overrides[get_semantic_retrieval_service] = lambda: fake_retriever

    client = TestClient(app)

    evaluation_case_id = fake_transaction.retrieval_evaluation_cases.evaluation_case.id

    response = client.post(
        "/api/v1/evaluation/runs",
        json={
            "evaluation_case_ids": [str(evaluation_case_id)],
            "top_k": 5,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload["results"]) == 1

    result = payload["results"][0]

    assert result["evaluation_case_id"] == str(evaluation_case_id)
    assert result["status"] == "succeeded"
    assert result["hit_count"] == 1
    assert result["recall_at_k"] == 1.0
    assert result["reciprocal_rank"] == 1.0

    summary = payload["summary"]

    assert summary["case_count"] == 1
    assert summary["succeeded_count"] == 1
    assert summary["failed_count"] == 0
    assert summary["hit_count"] == 1
    assert summary["total_expected_count"] == 1
    assert summary["hit_rate_at_k"] == 1.0
    assert summary["mean_recall_at_k"] == 1.0
    assert summary["mean_reciprocal_rank"] == 1.0

    assert len(fake_transaction.retrieval_evaluation_case_results.results) == 1
    assert fake_transaction.commit_count == 1

    assert len(fake_retriever.queries) == 1
    assert fake_retriever.queries[0].query == "What is Project Atlas status?"
    assert fake_retriever.queries[0].top_k == 5
    assert fake_retriever.queries[0].provider == "fake"
    assert fake_retriever.queries[0].model_name == "fake-embedding-v1"


def test_run_retrieval_evaluation_returns_404_for_missing_case() -> None:
    fake_transaction = FakeTransaction()
    fake_retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction
    app.dependency_overrides[get_semantic_retrieval_service] = lambda: fake_retriever

    client = TestClient(app)

    missing_case_id = uuid4()

    response = client.post(
        "/api/v1/evaluation/runs",
        json={
            "evaluation_case_ids": [str(missing_case_id)],
            "top_k": 5,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        f"Retrieval evaluation case not found: {missing_case_id}"
    )
    assert fake_transaction.retrieval_evaluation_case_results.results == []
    assert fake_transaction.commit_count == 0


def test_run_retrieval_evaluation_validates_empty_case_ids() -> None:
    fake_transaction = FakeTransaction()
    fake_retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction
    app.dependency_overrides[get_semantic_retrieval_service] = lambda: fake_retriever

    client = TestClient(app)

    response = client.post(
        "/api/v1/evaluation/runs",
        json={
            "evaluation_case_ids": [],
            "top_k": 5,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 422


def test_run_retrieval_evaluation_validates_top_k() -> None:
    fake_transaction = FakeTransaction()
    fake_retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction
    app.dependency_overrides[get_semantic_retrieval_service] = lambda: fake_retriever

    client = TestClient(app)

    evaluation_case_id = fake_transaction.retrieval_evaluation_cases.evaluation_case.id

    response = client.post(
        "/api/v1/evaluation/runs",
        json={
            "evaluation_case_ids": [str(evaluation_case_id)],
            "top_k": 0,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 422


def test_run_retrieval_evaluation_validates_blank_provider() -> None:
    fake_transaction = FakeTransaction()
    fake_retriever = FakeSemanticRetriever(retrieved_chunk_version_ids=())

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction
    app.dependency_overrides[get_semantic_retrieval_service] = lambda: fake_retriever

    client = TestClient(app)

    evaluation_case_id = fake_transaction.retrieval_evaluation_cases.evaluation_case.id

    response = client.post(
        "/api/v1/evaluation/runs",
        json={
            "evaluation_case_ids": [str(evaluation_case_id)],
            "top_k": 5,
            "provider": "",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 422