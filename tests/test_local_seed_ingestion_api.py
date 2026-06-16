from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes.ingestion import (
    get_document_ingestion_transaction,
    get_local_seed_document_ingestion_service,
)
from app.application.services.local_seed_document_ingestion_service import (
    LocalSeedDocumentIngestionAction,
    LocalSeedDocumentIngestionItem,
    LocalSeedDocumentIngestionResult,
)
from app.domain.documents.enums import IngestionRunStatus, SourceSystem
from app.main import create_app


class FakeLocalSeedDocumentIngestionService:
    def ingest(self, transaction: object) -> LocalSeedDocumentIngestionResult:
        return LocalSeedDocumentIngestionResult(
            run_id=uuid4(),
            source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
            source_path="seed_documents",
            status=IngestionRunStatus.COMPLETED,
            documents_seen=1,
            documents_changed=1,
            sections_created=2,
            chunks_created=3,
            embeddings_created=3,
            embeddings_reused=0,
            embedding_tokens_processed=42,
            estimated_embedding_cost_usd_micros=0,
            documents=(
                LocalSeedDocumentIngestionItem(
                    external_id="project-atlas-status.md",
                    title="Project Atlas Status",
                    action=LocalSeedDocumentIngestionAction.CREATED,
                    source_document_id=uuid4(),
                    document_version_id=uuid4(),
                    version_number=1,
                    content_checksum="content-checksum",
                    sections_created=2,
                    chunks_created=3,
                    embeddings_created=3,
                    embeddings_reused=0,
                    embedding_tokens_processed=42,
                    estimated_embedding_cost_usd_micros=0,
                ),
            ),
        )


def test_ingest_local_seed_documents_returns_ingestion_result() -> None:
    app = create_app()
    app.dependency_overrides[get_local_seed_document_ingestion_service] = (
        lambda: FakeLocalSeedDocumentIngestionService()
    )
    app.dependency_overrides[get_document_ingestion_transaction] = lambda: object()

    client = TestClient(app)

    response = client.post("/api/v1/ingestion/local-seed-documents/runs")

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_system"] == "local_seed_documents"
    assert payload["source_path"] == "seed_documents"
    assert payload["status"] == "completed"
    assert payload["documents_seen"] == 1
    assert payload["documents_changed"] == 1
    assert payload["sections_created"] == 2
    assert payload["chunks_created"] == 3
    assert payload["embeddings_created"] == 3
    assert payload["embeddings_reused"] == 0
    assert payload["embedding_tokens_processed"] == 42
    assert payload["estimated_embedding_cost_usd_micros"] == 0
    assert payload["documents"][0]["external_id"] == "project-atlas-status.md"
    assert payload["documents"][0]["action"] == "created"
    assert payload["documents"][0]["version_number"] == 1
    assert payload["documents"][0]["sections_created"] == 2
    assert payload["documents"][0]["chunks_created"] == 3
    assert payload["documents"][0]["embeddings_reused"] == 0
    assert payload["documents"][0]["embeddings_created"] == 3
    assert payload["documents"][0]["embedding_tokens_processed"] == 42
    assert payload["documents"][0]["estimated_embedding_cost_usd_micros"] == 0
    assert "raw_content" not in payload["documents"][0]

    app.dependency_overrides.clear()