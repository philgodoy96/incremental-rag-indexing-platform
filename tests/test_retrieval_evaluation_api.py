from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_answering_transaction
from app.domain.evaluation.entities import (
    RetrievalEvaluationCase,
    RetrievalEvaluationCaseResult,
)
from app.main import create_app


class FakeRetrievalEvaluationCaseRepository:
    def __init__(self) -> None:
        self.evaluation_case = RetrievalEvaluationCase.create(
            name="Project Atlas status",
            query="What is Project Atlas status?",
            expected_chunk_version_ids=(uuid4(),),
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
    def __init__(self, evaluation_case: RetrievalEvaluationCase) -> None:
        self.result = RetrievalEvaluationCaseResult.succeeded(
            evaluation_case=evaluation_case,
            retrieved_chunk_version_ids=(
                evaluation_case.expected_chunk_version_ids[0],
            ),
            top_k=5,
        )

    def get_by_id(
        self,
        evaluation_case_result_id: UUID,
    ) -> RetrievalEvaluationCaseResult | None:
        if evaluation_case_result_id != self.result.id:
            return None

        return self.result

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> list[RetrievalEvaluationCaseResult]:
        results = [self.result]

        if status is not None:
            results = [result for result in results if result.status.value == status]

        return results[offset : offset + limit]

    def list_by_case_id(
        self,
        evaluation_case_id: UUID,
    ) -> list[RetrievalEvaluationCaseResult]:
        if evaluation_case_id != self.result.evaluation_case_id:
            return []

        return [self.result]

    def save(self, result: RetrievalEvaluationCaseResult) -> None:
        self.result = result

    def save_many(self, results: list[RetrievalEvaluationCaseResult]) -> None:
        if results:
            self.result = results[0]


class FakeTransaction:
    def __init__(self) -> None:
        self.retrieval_evaluation_cases = FakeRetrievalEvaluationCaseRepository()
        self.retrieval_evaluation_case_results = (
            FakeRetrievalEvaluationCaseResultRepository(
                self.retrieval_evaluation_cases.evaluation_case,
            )
        )
        self.commit_count = 0

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.commit_count += 1


def test_create_retrieval_evaluation_case() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    expected_chunk_id = uuid4()

    response = client.post(
        "/api/v1/evaluation/cases",
        json={
            "name": "Project Atlas owner",
            "query": "Who owns Project Atlas?",
            "expected_chunk_version_ids": [str(expected_chunk_id)],
            "tags": ["ownership", "project-atlas"],
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["id"]
    assert payload["name"] == "Project Atlas owner"
    assert payload["query"] == "Who owns Project Atlas?"
    assert payload["expected_chunk_version_ids"] == [str(expected_chunk_id)]
    assert payload["tags"] == ["ownership", "project-atlas"]

    assert fake_transaction.retrieval_evaluation_cases.evaluation_case.name == (
        "Project Atlas owner"
    )
    assert fake_transaction.commit_count == 1


def test_list_retrieval_evaluation_cases() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/evaluation/cases")

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == str(
        fake_transaction.retrieval_evaluation_cases.evaluation_case.id,
    )
    assert payload["items"][0]["name"] == "Project Atlas status"


def test_list_retrieval_evaluation_cases_filters_by_tag() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/evaluation/cases?tag=status")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload["items"]) == 1
    assert payload["items"][0]["tags"] == ["status", "project-atlas"]


def test_get_retrieval_evaluation_case() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    evaluation_case_id = fake_transaction.retrieval_evaluation_cases.evaluation_case.id

    response = client.get(f"/api/v1/evaluation/cases/{evaluation_case_id}")

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(evaluation_case_id)
    assert payload["name"] == "Project Atlas status"


def test_get_retrieval_evaluation_case_returns_404() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/evaluation/cases/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Retrieval evaluation case not found"


def test_list_retrieval_evaluation_results() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/evaluation/results")

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == str(
        fake_transaction.retrieval_evaluation_case_results.result.id,
    )
    assert payload["items"][0]["status"] == "succeeded"
    assert payload["items"][0]["hit_count"] == 1
    assert payload["items"][0]["recall_at_k"] == 1.0
    assert payload["items"][0]["reciprocal_rank"] == 1.0


def test_get_retrieval_evaluation_result() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    result_id = fake_transaction.retrieval_evaluation_case_results.result.id

    response = client.get(f"/api/v1/evaluation/results/{result_id}")

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(result_id)
    assert payload["status"] == "succeeded"


def test_get_retrieval_evaluation_result_returns_404() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/evaluation/results/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Retrieval evaluation case result not found"


def test_list_retrieval_evaluation_results_for_case() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    evaluation_case_id = fake_transaction.retrieval_evaluation_cases.evaluation_case.id

    response = client.get(
        f"/api/v1/evaluation/cases/{evaluation_case_id}/results",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["evaluation_case_id"] == str(evaluation_case_id)


def test_list_retrieval_evaluation_results_for_missing_case_returns_404() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/evaluation/cases/{uuid4()}/results")

    assert response.status_code == 404
    assert response.json()["detail"] == "Retrieval evaluation case not found"


def test_list_retrieval_evaluation_cases_validates_limit() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/evaluation/cases?limit=999")

    assert response.status_code == 422


def test_create_retrieval_evaluation_case_validates_expected_chunks() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.post(
        "/api/v1/evaluation/cases",
        json={
            "name": "Invalid case",
            "query": "What is Project Atlas status?",
            "expected_chunk_version_ids": [],
            "tags": [],
        },
    )

    assert response.status_code == 422