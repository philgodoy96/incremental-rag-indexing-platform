from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_grounded_answer_service,
    get_retrieval_transaction,
)
from app.domain.answering.entities import (
    GroundedAnswer,
    GroundedAnswerCitation,
    GroundedAnswerRequest,
)
from app.main import create_app


class FakeGroundedAnswerService:
    def __init__(self, answer: GroundedAnswer) -> None:
        self.answer_result = answer
        self.last_request: GroundedAnswerRequest | None = None

    def answer(
        self,
        *,
        request: GroundedAnswerRequest,
        transaction: object,
    ) -> GroundedAnswer:
        self.last_request = request
        return self.answer_result


class FakeTransaction:
    pass


def make_citation() -> GroundedAnswerCitation:
    return GroundedAnswerCitation(
        rank=1,
        vector_index_entry_id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        chunk_index=0,
        heading_context=("Project Atlas Status", "Summary"),
        quote="Status: At Risk",
        distance=0.12,
    )


def test_create_grounded_answer_returns_answer_with_citations() -> None:
    fake_service = FakeGroundedAnswerService(
        GroundedAnswer.answered(
            question="What is Project Atlas status?",
            answer="Project Atlas is at risk.",
            query_trace_id=uuid4(),
            citations=(make_citation(),),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_retrieval_transaction] = lambda: FakeTransaction()

    client = TestClient(app)

    response = client.post(
        "/api/v1/answers",
        json={
            "question": "What is Project Atlas status?",
            "top_k": 5,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["question"] == "What is Project Atlas status?"
    assert payload["answer"] == "Project Atlas is at risk."
    assert payload["status"] == "answered"
    assert payload["query_trace_id"]
    assert len(payload["citations"]) == 1
    assert payload["citations"][0]["rank"] == 1
    assert payload["citations"][0]["stable_section_key"] == (
        "project-atlas-status/summary"
    )
    assert payload["citations"][0]["quote"] == "Status: At Risk"
    assert payload["citations"][0]["distance"] == 0.12

    assert fake_service.last_request is not None
    assert fake_service.last_request.question == "What is Project Atlas status?"
    assert fake_service.last_request.top_k == 5
    assert fake_service.last_request.provider == "fake"
    assert fake_service.last_request.model_name == "fake-embedding-v1"


def test_create_grounded_answer_returns_insufficient_context() -> None:
    fake_service = FakeGroundedAnswerService(
        GroundedAnswer.insufficient_context(
            question="What is Project Phoenix budget?",
            query_trace_id=uuid4(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_retrieval_transaction] = lambda: FakeTransaction()

    client = TestClient(app)

    response = client.post(
        "/api/v1/answers",
        json={
            "question": "What is Project Phoenix budget?",
            "top_k": 5,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["question"] == "What is Project Phoenix budget?"
    assert payload["status"] == "insufficient_context"
    assert payload["citations"] == []
    assert "not have enough retrieved context" in payload["answer"]


def test_create_grounded_answer_validates_blank_question() -> None:
    fake_service = FakeGroundedAnswerService(
        GroundedAnswer.insufficient_context(
            question="unused",
            query_trace_id=uuid4(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_retrieval_transaction] = lambda: FakeTransaction()

    client = TestClient(app)

    response = client.post(
        "/api/v1/answers",
        json={
            "question": "",
            "top_k": 5,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 422


def test_create_grounded_answer_validates_top_k() -> None:
    fake_service = FakeGroundedAnswerService(
        GroundedAnswer.insufficient_context(
            question="unused",
            query_trace_id=uuid4(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_retrieval_transaction] = lambda: FakeTransaction()

    client = TestClient(app)

    response = client.post(
        "/api/v1/answers",
        json={
            "question": "What is Project Atlas status?",
            "top_k": 999,
            "provider": "fake",
            "model_name": "fake-embedding-v1",
        },
    )

    assert response.status_code == 422