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

        if status is not None:
            records = [record for record in records if record.status.value == status]

        if provider is not None:
            records = [record for record in records if record.provider == provider]

        if model_name is not None:
            records = [
                record for record in records if record.model_name == model_name
            ]

        return records[offset : offset + limit]

    def save(self, answer: AnswerRecord) -> None:
        self.answer = answer


class FakeLLMProviderCallRecordRepository:
    def __init__(self, answer_id: UUID) -> None:
        succeeded_started_at = datetime.now(UTC)
        succeeded_completed_at = succeeded_started_at + timedelta(milliseconds=125)

        failed_started_at = succeeded_started_at + timedelta(seconds=1)
        failed_completed_at = failed_started_at + timedelta(milliseconds=75)

        self.succeeded_record = LLMProviderCallRecord.succeeded(
            answer_id=answer_id,
            query_trace_id=uuid4(),
            provider="fake",
            model_name="fake-llm-v1",
            prompt_tokens=10,
            completion_tokens=5,
            estimated_cost_usd=Decimal("0.0001"),
            started_at=succeeded_started_at,
            completed_at=succeeded_completed_at,
        )
        self.failed_record = LLMProviderCallRecord.failed(
            answer_id=None,
            query_trace_id=uuid4(),
            provider="fake",
            model_name="fake-llm-v1",
            error_message="provider timeout",
            started_at=failed_started_at,
            completed_at=failed_completed_at,
        )
        self.records = {
            self.succeeded_record.id: self.succeeded_record,
            self.failed_record.id: self.failed_record,
        }

    def get_by_id(
        self,
        provider_call_id: UUID,
    ) -> LLMProviderCallRecord | None:
        return self.records.get(provider_call_id)

    def list_recent(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMProviderCallRecord]:
        records = list(self.records.values())

        if status is not None:
            records = [record for record in records if record.status.value == status]

        if provider is not None:
            records = [record for record in records if record.provider == provider]

        if model_name is not None:
            records = [
                record for record in records if record.model_name == model_name
            ]

        records = sorted(records, key=lambda record: record.started_at, reverse=True)

        return records[offset : offset + limit]

    def list_by_answer_id(
        self,
        answer_id: UUID,
    ) -> list[LLMProviderCallRecord]:
        return sorted(
            [
                record
                for record in self.records.values()
                if record.answer_id == answer_id
            ],
            key=lambda record: record.started_at,
        )

    def save(self, record: LLMProviderCallRecord) -> None:
        self.records[record.id] = record


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
    assert len(payload["items"]) == 2

    first_item = payload["items"][0]
    second_item = payload["items"][1]

    assert first_item["id"] == str(fake_transaction.llm_provider_calls.failed_record.id)
    assert first_item["status"] == "failed"

    assert second_item["id"] == str(
        fake_transaction.llm_provider_calls.succeeded_record.id,
    )
    assert second_item["answer_id"] == str(fake_transaction.answer_id)
    assert second_item["provider"] == "fake"
    assert second_item["model_name"] == "fake-llm-v1"
    assert second_item["status"] == "succeeded"
    assert second_item["prompt_tokens"] == 10
    assert second_item["completion_tokens"] == 5
    assert second_item["total_tokens"] == 15
    assert second_item["estimated_cost_usd"] == "0.0001"
    assert second_item["latency_ms"] == 125
    assert second_item["error_message"] is None


def test_list_llm_provider_calls_filters_failed_records() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/llm-provider-calls?status=failed")

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 20
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1

    item = payload["items"][0]

    assert item["id"] == str(fake_transaction.llm_provider_calls.failed_record.id)
    assert item["answer_id"] is None
    assert item["provider"] == "fake"
    assert item["model_name"] == "fake-llm-v1"
    assert item["status"] == "failed"
    assert item["prompt_tokens"] == 0
    assert item["completion_tokens"] == 0
    assert item["total_tokens"] == 0
    assert item["estimated_cost_usd"] == "0"
    assert item["latency_ms"] == 75
    assert item["error_message"] == "provider timeout"


def test_get_llm_provider_call_returns_succeeded_record_by_id() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        "/api/v1/llm-provider-calls/"
        f"{fake_transaction.llm_provider_calls.succeeded_record.id}",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(
        fake_transaction.llm_provider_calls.succeeded_record.id,
    )
    assert payload["answer_id"] == str(fake_transaction.answer_id)
    assert payload["provider"] == "fake"
    assert payload["model_name"] == "fake-llm-v1"
    assert payload["status"] == "succeeded"


def test_get_llm_provider_call_returns_failed_record_by_id() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        "/api/v1/llm-provider-calls/"
        f"{fake_transaction.llm_provider_calls.failed_record.id}",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(fake_transaction.llm_provider_calls.failed_record.id)
    assert payload["answer_id"] is None
    assert payload["provider"] == "fake"
    assert payload["model_name"] == "fake-llm-v1"
    assert payload["status"] == "failed"
    assert payload["prompt_tokens"] == 0
    assert payload["completion_tokens"] == 0
    assert payload["total_tokens"] == 0
    assert payload["estimated_cost_usd"] == "0"
    assert payload["latency_ms"] == 75
    assert payload["error_message"] == "provider timeout"


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
    assert payload["items"][0]["status"] == "succeeded"


def test_list_llm_provider_calls_for_missing_answer_returns_404() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(f"/api/v1/answers/{uuid4()}/llm-provider-calls")

    assert response.status_code == 404
    assert response.json()["detail"] == "Answer not found"