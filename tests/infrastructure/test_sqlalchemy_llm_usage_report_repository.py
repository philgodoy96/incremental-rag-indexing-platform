from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from app.infrastructure.repositories.sqlalchemy_llm_observability_repositories import (
    SqlAlchemyLLMUsageReportRepository,
)


class FakeExecuteResult:
    def __init__(self, *, one_result: object | None = None) -> None:
        self._one_result = one_result

    def one(self) -> object:
        if self._one_result is None:
            raise AssertionError("one_result was not configured")

        return self._one_result


class FakeExecuteListResult:
    def __init__(self, *, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        return self._rows


class FakeSession:
    def __init__(self, result: object) -> None:
        self.result = result
        self.executed_statements: list[object] = []

    def execute(self, statement: object) -> object:
        self.executed_statements.append(statement)

        return self.result


def test_sqlalchemy_llm_usage_report_repository_maps_empty_summary() -> None:
    row = SimpleNamespace(
        call_count=0,
        succeeded_count=None,
        failed_count=None,
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
        estimated_cost_usd=None,
        average_latency_ms=None,
    )
    session = FakeSession(FakeExecuteResult(one_result=row))
    repository = SqlAlchemyLLMUsageReportRepository(session)  # type: ignore[arg-type]

    summary = repository.summarize()

    assert summary.call_count == 0
    assert summary.succeeded_count == 0
    assert summary.failed_count == 0
    assert summary.prompt_tokens == 0
    assert summary.completion_tokens == 0
    assert summary.total_tokens == 0
    assert summary.estimated_cost_usd == Decimal("0")
    assert summary.average_latency_ms == 0.0
    assert len(session.executed_statements) == 1


def test_sqlalchemy_llm_usage_report_repository_maps_summary() -> None:
    row = SimpleNamespace(
        call_count=3,
        succeeded_count=2,
        failed_count=1,
        prompt_tokens=100,
        completion_tokens=40,
        total_tokens=140,
        estimated_cost_usd=Decimal("0.0123"),
        average_latency_ms=125.5,
    )
    session = FakeSession(FakeExecuteResult(one_result=row))
    repository = SqlAlchemyLLMUsageReportRepository(session)  # type: ignore[arg-type]

    summary = repository.summarize(provider="fake", model_name="fake-llm-v1")

    assert summary.call_count == 3
    assert summary.succeeded_count == 2
    assert summary.failed_count == 1
    assert summary.prompt_tokens == 100
    assert summary.completion_tokens == 40
    assert summary.total_tokens == 140
    assert summary.estimated_cost_usd == Decimal("0.0123")
    assert summary.average_latency_ms == 125.5
    assert len(session.executed_statements) == 1


def test_sqlalchemy_llm_usage_report_repository_maps_by_model_summary() -> None:
    rows: list[Any] = [
        SimpleNamespace(
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
        SimpleNamespace(
            provider="fake",
            model_name="fake-llm-v2",
            call_count=1,
            succeeded_count=1,
            failed_count=0,
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30,
            estimated_cost_usd=Decimal("0.001"),
            average_latency_ms=75,
        ),
    ]
    session = FakeSession(FakeExecuteListResult(rows=rows))
    repository = SqlAlchemyLLMUsageReportRepository(session)  # type: ignore[arg-type]

    summaries = repository.summarize_by_model(provider="fake")

    assert len(summaries) == 2

    first = summaries[0]
    second = summaries[1]

    assert first.provider == "fake"
    assert first.model_name == "fake-llm-v1"
    assert first.call_count == 3
    assert first.succeeded_count == 2
    assert first.failed_count == 1
    assert first.prompt_tokens == 100
    assert first.completion_tokens == 40
    assert first.total_tokens == 140
    assert first.estimated_cost_usd == Decimal("0.0123")
    assert first.average_latency_ms == 125.5

    assert second.provider == "fake"
    assert second.model_name == "fake-llm-v2"
    assert second.call_count == 1
    assert second.succeeded_count == 1
    assert second.failed_count == 0
    assert second.prompt_tokens == 20
    assert second.completion_tokens == 10
    assert second.total_tokens == 30
    assert second.estimated_cost_usd == Decimal("0.001")
    assert second.average_latency_ms == 75.0

    assert len(session.executed_statements) == 1