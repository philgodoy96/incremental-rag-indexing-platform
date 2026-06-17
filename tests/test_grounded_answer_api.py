from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_answering_transaction,
    get_grounded_answer_service,
)
from app.domain.answering.entities import (
    AnswerCitationRecord,
    AnswerRecord,
    GroundedAnswer,
    GroundedAnswerCitation,
    GroundedAnswerRequest,
)
from app.domain.answering.enums import GroundedAnswerStatus
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


class FakeAnswerRecordRepository:
    def __init__(self) -> None:
        self.answer_id = uuid4()

        self.answer = AnswerRecord(
            id=self.answer_id,
            question="What is Project Atlas status?",
            answer="Project Atlas is at risk.",
            status=GroundedAnswerStatus.ANSWERED,
            query_trace_id=uuid4(),
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
            created_at=datetime.now(UTC),
        )

    def get_by_id(self, answer_id: UUID) -> AnswerRecord | None:
        if answer_id != self.answer_id:
            return None

        return self.answer

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[AnswerRecord]:
        answers = [self.answer]

        if status is not None:
            answers = [answer for answer in answers if answer.status.value == status]

        if provider is not None:
            answers = [answer for answer in answers if answer.provider == provider]

        if model_name is not None:
            answers = [
                answer for answer in answers if answer.model_name == model_name
            ]

        return answers[offset : offset + limit]

    def save(self, answer: AnswerRecord) -> None:
        self.answer = answer
        self.answer_id = answer.id


class FakeAnswerCitationRecordRepository:
    def __init__(self, answer_id: UUID) -> None:
        self.citation = AnswerCitationRecord(
            id=uuid4(),
            answer_id=answer_id,
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
            created_at=datetime.now(UTC),
        )

    def list_by_answer_id(self, answer_id: UUID) -> list[AnswerCitationRecord]:
        if answer_id != self.citation.answer_id:
            return []

        return [self.citation]

    def save_many(self, citations: list[AnswerCitationRecord]) -> None:
        if citations:
            self.citation = citations[0]


class FakeTransaction:
    def __init__(self) -> None:
        self.answer_records = FakeAnswerRecordRepository()
        self.answer_citation_records = FakeAnswerCitationRecordRepository(
            self.answer_records.answer_id,
        )

    def flush(self) -> None:
        pass

    def commit(self) -> None:
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
            answer_id=uuid4(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_answering_transaction] = lambda: FakeTransaction()

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
    assert payload["answer_id"]
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
            answer_id=uuid4(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_answering_transaction] = lambda: FakeTransaction()

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
    assert payload["answer_id"]
    assert payload["citations"] == []
    assert "not have enough retrieved context" in payload["answer"]


def test_create_grounded_answer_validates_blank_question() -> None:
    fake_service = FakeGroundedAnswerService(
        GroundedAnswer.insufficient_context(
            question="unused",
            query_trace_id=uuid4(),
            answer_id=uuid4(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_answering_transaction] = lambda: FakeTransaction()

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
            answer_id=uuid4(),
        ),
    )

    app = create_app()
    app.dependency_overrides[get_grounded_answer_service] = lambda: fake_service
    app.dependency_overrides[get_answering_transaction] = lambda: FakeTransaction()

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


def test_list_answers_returns_recent_answers() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/answers")

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == str(fake_transaction.answer_records.answer_id)
    assert payload["items"][0]["question"] == "What is Project Atlas status?"
    assert payload["items"][0]["answer"] == "Project Atlas is at risk."
    assert payload["items"][0]["status"] == "answered"
    assert payload["items"][0]["top_k"] == 5
    assert payload["items"][0]["provider"] == "fake"
    assert payload["items"][0]["model_name"] == "fake-embedding-v1"


def test_get_answer_returns_answer_with_citations() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        f"/api/v1/answers/{fake_transaction.answer_records.answer_id}",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(fake_transaction.answer_records.answer_id)
    assert payload["question"] == "What is Project Atlas status?"
    assert payload["answer"] == "Project Atlas is at risk."
    assert payload["status"] == "answered"
    assert payload["query_trace_id"]
    assert len(payload["citations"]) == 1
    assert payload["citations"][0]["rank"] == 1
    assert payload["citations"][0]["quote"] == "Status: At Risk"
    assert payload["citations"][0]["distance"] == 0.12


def test_get_answer_returns_404_for_missing_answer() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/answers/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Answer not found"


def test_list_answers_validates_limit() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/answers?limit=999")

    assert response.status_code == 422