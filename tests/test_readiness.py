from fastapi.testclient import TestClient

from app.api.routes.readiness import get_database_readiness_service
from app.application.services.database_readiness_service import (
    DatabaseReadinessError,
    DatabaseReadinessResult,
)
from app.main import create_app


class FakeReadyDatabaseReadinessService:
    def check(self) -> DatabaseReadinessResult:
        return DatabaseReadinessResult(
            database_status="ok",
            pgvector_status="ok",
        )


class FakeFailingDatabaseReadinessService:
    def check(self) -> DatabaseReadinessResult:
        raise DatabaseReadinessError("database unavailable")


def test_readiness_check_returns_ready_when_database_dependencies_are_available() -> None:
    app = create_app()
    app.dependency_overrides[get_database_readiness_service] = (
        lambda: FakeReadyDatabaseReadinessService()
    )

    client = TestClient(app)

    response = client.get("/api/v1/readiness")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"
    assert payload["database"] == "ok"
    assert payload["pgvector_extension"] == "ok"
    assert "timestamp_utc" in payload

    app.dependency_overrides.clear()


def test_readiness_check_returns_503_when_database_dependencies_are_unavailable() -> None:
    app = create_app()
    app.dependency_overrides[get_database_readiness_service] = (
        lambda: FakeFailingDatabaseReadinessService()
    )

    client = TestClient(app)

    response = client.get("/api/v1/readiness")

    assert response.status_code == 503

    payload = response.json()

    assert payload["detail"]["status"] == "not_ready"
    assert payload["detail"]["reason"] == "database unavailable"

    app.dependency_overrides.clear()