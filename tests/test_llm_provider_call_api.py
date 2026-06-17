from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import get_answering_transaction
from app.domain.answering.entities import AnswerRecord
from app.domain.answering.enums import GroundedAnswerStatus
from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.main import create_app


class FakeAnswerRecordRepository:
    def __init__(self, answer_id: UUID) -> None:
        self.answer = AnswerRecord(
            id=answer_id,
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
        if answer_id != self.answer.id:
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
        records = [self.answer]

        return records[offset : offset + limit]

    def save(self, answer: AnswerRecord) -> None:
        self.answer = answer


class FakeLLMProviderCallRecordRepository:
    def __init__(self, answer_id: UUID) -> None:
        started_at = datetime.now(UTC)
        completed_at = started_at + timedelta(milliseconds=125)

        self.record = LLMProviderCallRecord.succeeded(
            answer_id=answer_id,
            query_trace_id=uuid4(),
            provider="fake",
            model_name="fake-llm-v1",
            prompt_tokens=10,
            completion_tokens=5,
            estimated_cost_usd=Decimal("0.0001"),
            started_at=started_at,
            completed_at=completed_at,
        )

    def get_by_id(
        self,
        provider_call_id: UUID,
    ) -> LLMProviderCallRecord | None:
        if provider_call_id != self.record.id:
            return None

        return self.record

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMProviderCallRecord]:
        records = [self.record]

        if status is not None:
            records = [record for record in records if record.status.value == status]

        if provider is not None:
            records = [record for record in records if record.provider == provider]

        if model_name is not None:
            records = [
                record for record in records if record.model_name == model_name
            ]

        return records[offset : offset + limit]

    def list_by_answer_id(
        self,
        answer_id: UUID,
    ) -> list[LLMProviderCallRecord]:
        if answer_id != self.record.answer_id:
            return []

        return [self.record]

    def save(self, record: LLMProviderCallRecord) -> None:
        self.record = record


class FakeTransaction:
    def __init__(self) -> None:
        self.answer_id = uuid4()
        self.answer_records = FakeAnswerRecordRepository(self.answer_id)
        self.llm_provider_calls = FakeLLMProviderCallRecordRepository(self.answer_id)

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        pass


def test_list_llm_provider_calls_returns_recent_records() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/llm-provider-calls")

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert item["id"] == str(fake_transaction.llm_provider_calls.record.id)
    assert item["answer_id"] == str(fake_transaction.answer_id)
    assert item["provider"] == "fake"
    assert item["model_name"] == "fake-llm-v1"
    assert item["status"] == "succeeded"
    assert item["prompt_tokens"] == 10
    assert item["completion_tokens"] == 5
    assert item["total_tokens"] == 15
    assert item["estimated_cost_usd"] == "0.0001"
    assert item["latency_ms"] == 125
    assert item["error_message"] is None


def test_get_llm_provider_call_returns_record_by_id() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        f"/api/v1/llm-provider-calls/{fake_transaction.llm_provider_calls.record.id}",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(fake_transaction.llm_provider_calls.record.id)
    assert payload["answer_id"] == str(fake_transaction.answer_id)
    assert payload["provider"] == "fake"
    assert payload["model_name"] == "fake-llm-v1"
    assert payload["status"] == "succeeded"


def test_get_llm_provider_call_returns_404_for_missing_record() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/llm-provider-calls/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "LLM provider call not found"


def test_list_llm_provider_calls_validates_limit() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/llm-provider-calls?limit=999")

    assert response.status_code == 422


def test_list_llm_provider_calls_for_answer_returns_records() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        f"/api/v1/answers/{fake_transaction.answer_id}/llm-provider-calls",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["answer_id"] == str(fake_transaction.answer_id)


def test_list_llm_provider_calls_for_missing_answer_returns_404() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/answers/{uuid4()}/llm-provider-calls")

    assert response.status_code == 404
    assert response.json()["detail"] == "Answer not found"
