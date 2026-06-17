from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.dependencies import get_answering_transaction
from app.domain.llm_observability.usage_reports import (
    LLMUsageByModelSummary,
    LLMUsageSummary,
)
from app.main import create_app


class FakeLLMUsageReportRepository:
    def __init__(self) -> None:
        self.last_summary_filters: dict[str, object] | None = None
        self.last_by_model_filters: dict[str, object] | None = None

    def summarize(
        self,
        *,
        started_at_from: datetime | None = None,
        started_at_to: datetime | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> LLMUsageSummary:
        self.last_summary_filters = {
            "started_at_from": started_at_from,
            "started_at_to": started_at_to,
            "provider": provider,
            "model_name": model_name,
        }

        return LLMUsageSummary(
            call_count=3,
            succeeded_count=2,
            failed_count=1,
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=140,
            estimated_cost_usd=Decimal("0.0123"),
            average_latency_ms=125.5,
        )

    def summarize_by_model(
        self,
        *,
        started_at_from: datetime | None = None,
        started_at_to: datetime | None = None,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> list[LLMUsageByModelSummary]:
        self.last_by_model_filters = {
            "started_at_from": started_at_from,
            "started_at_to": started_at_to,
            "provider": provider,
            "model_name": model_name,
        }

        return [
            LLMUsageByModelSummary(
                provider="fake",
                model_name="fake-llm-v1",
                call_count=3,
                succeeded_count=2,
                failed_count=1,
                prompt_tokens=100,
                completion_tokens=40,
                total_tokens=140,
                estimated_cost_usd=Decimal("0.0123"),
                average_latency_ms=125.5,
            ),
            LLMUsageByModelSummary(
                provider="fake",
                model_name="fake-llm-v2",
                call_count=1,
                succeeded_count=1,
                failed_count=0,
                prompt_tokens=20,
                completion_tokens=10,
                total_tokens=30,
                estimated_cost_usd=Decimal("0.001"),
                average_latency_ms=75.0,
            ),
        ]


class FakeTransaction:
    def __init__(self) -> None:
        self.llm_usage_reports = FakeLLMUsageReportRepository()

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        pass


def test_get_llm_usage_summary_returns_aggregates() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/llm-usage/summary")

    assert response.status_code == 200

    payload = response.json()

    assert payload["call_count"] == 3
    assert payload["succeeded_count"] == 2
    assert payload["failed_count"] == 1
    assert payload["prompt_tokens"] == 100
    assert payload["completion_tokens"] == 40
    assert payload["total_tokens"] == 140
    assert payload["estimated_cost_usd"] == "0.0123"
    assert payload["average_latency_ms"] == 125.5


def test_get_llm_usage_summary_forwards_filters() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        "/api/v1/llm-usage/summary"
        "?provider=fake"
        "&model_name=fake-llm-v1"
        "&started_at_from=2026-06-17T00:00:00Z"
        "&started_at_to=2026-06-18T00:00:00Z",
    )

    assert response.status_code == 200

    filters = fake_transaction.llm_usage_reports.last_summary_filters

    assert filters is not None
    assert filters["provider"] == "fake"
    assert filters["model_name"] == "fake-llm-v1"
    assert filters["started_at_from"] == datetime(
        2026,
        6,
        17,
        0,
        0,
        0,
        tzinfo=UTC,
    )
    assert filters["started_at_to"] == datetime(
        2026,
        6,
        18,
        0,
        0,
        0,
        tzinfo=UTC,
    )


def test_get_llm_usage_by_model_returns_aggregates() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/llm-usage/by-model")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload["items"]) == 2

    first = payload["items"][0]
    second = payload["items"][1]

    assert first["provider"] == "fake"
    assert first["model_name"] == "fake-llm-v1"
    assert first["call_count"] == 3
    assert first["succeeded_count"] == 2
    assert first["failed_count"] == 1
    assert first["prompt_tokens"] == 100
    assert first["completion_tokens"] == 40
    assert first["total_tokens"] == 140
    assert first["estimated_cost_usd"] == "0.0123"
    assert first["average_latency_ms"] == 125.5

    assert second["provider"] == "fake"
    assert second["model_name"] == "fake-llm-v2"
    assert second["call_count"] == 1
    assert second["succeeded_count"] == 1
    assert second["failed_count"] == 0
    assert second["prompt_tokens"] == 20
    assert second["completion_tokens"] == 10
    assert second["total_tokens"] == 30
    assert second["estimated_cost_usd"] == "0.001"
    assert second["average_latency_ms"] == 75.0


def test_get_llm_usage_by_model_forwards_filters() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get(
        "/api/v1/llm-usage/by-model"
        "?provider=fake"
        "&model_name=fake-llm-v1"
        "&started_at_from=2026-06-17T00:00:00Z"
        "&started_at_to=2026-06-18T00:00:00Z",
    )

    assert response.status_code == 200

    filters = fake_transaction.llm_usage_reports.last_by_model_filters

    assert filters is not None
    assert filters["provider"] == "fake"
    assert filters["model_name"] == "fake-llm-v1"
    assert filters["started_at_from"] == datetime(
        2026,
        6,
        17,
        0,
        0,
        0,
        tzinfo=UTC,
    )
    assert filters["started_at_to"] == datetime(
        2026,
        6,
        18,
        0,
        0,
        0,
        tzinfo=UTC,
    )


def test_get_llm_usage_summary_validates_blank_provider() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/llm-usage/summary?provider=")

    assert response.status_code == 422


def test_get_llm_usage_by_model_validates_blank_model_name() -> None:
    fake_transaction = FakeTransaction()

    app = create_app()
    app.dependency_overrides[get_answering_transaction] = lambda: fake_transaction

    client = TestClient(app)

    response = client.get("/api/v1/llm-usage/by-model?model_name=")

    assert response.status_code == 422