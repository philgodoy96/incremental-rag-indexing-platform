from fastapi.testclient import TestClient

from app.api.routes.ingestion import get_local_seed_document_discovery_service
from app.application.services.local_seed_document_discovery_service import (
    LocalSeedDocumentDiscoveryResult,
)
from app.domain.documents.enums import SourceSystem
from app.domain.documents.source_candidates import SourceDocumentCandidate
from app.main import create_app


class FakeLocalSeedDocumentDiscoveryService:
    def discover(self) -> LocalSeedDocumentDiscoveryResult:
        candidate = SourceDocumentCandidate.create(
            source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
            external_id="project-atlas-status.md",
            source_uri="seed_documents/project-atlas-status.md",
            title="Project Atlas Status",
            raw_content="# Project Atlas Status\n\nStatus: On Track\n",
        )

        return LocalSeedDocumentDiscoveryResult(
            source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
            source_path="seed_documents",
            documents=(candidate,),
        )


def test_discover_local_seed_documents_returns_discovered_documents() -> None:
    app = create_app()
    app.dependency_overrides[get_local_seed_document_discovery_service] = (
        lambda: FakeLocalSeedDocumentDiscoveryService()
    )

    client = TestClient(app)

    response = client.post("/api/v1/ingestion/local-seed-documents/discover")

    assert response.status_code == 200

    payload = response.json()

    assert payload["source_system"] == "local_seed_documents"
    assert payload["source_path"] == "seed_documents"
    assert payload["document_count"] == 1
    assert payload["documents"][0]["external_id"] == "project-atlas-status.md"
    assert payload["documents"][0]["source_uri"] == "seed_documents/project-atlas-status.md"
    assert payload["documents"][0]["title"] == "Project Atlas Status"
    assert "content_checksum" in payload["documents"][0]
    assert "metadata_checksum" in payload["documents"][0]
    assert "raw_content" not in payload["documents"][0]

    app.dependency_overrides.clear()