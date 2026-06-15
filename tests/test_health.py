from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_returns_ok() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "Incremental RAG Indexing Platform"
    assert payload["environment"] == "local"
    assert "timestamp_utc" in payload
