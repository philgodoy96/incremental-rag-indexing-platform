from pathlib import Path

from app.application.services.local_seed_document_discovery_service import (
    LocalSeedDocumentDiscoveryService,
)
from app.domain.documents.enums import SourceSystem


def test_local_seed_document_discovery_service_returns_discovery_result(
    tmp_path: Path,
) -> None:
    (tmp_path / "project-atlas-status.md").write_text(
        "# Project Atlas Status\n\nStatus: On Track\n",
        encoding="utf-8",
    )

    service = LocalSeedDocumentDiscoveryService(source_path=tmp_path)

    result = service.discover()

    assert result.source_system == SourceSystem.LOCAL_SEED_DOCUMENTS
    assert result.source_path == tmp_path.as_posix()
    assert result.document_count == 1
    assert result.documents[0].external_id == "project-atlas-status.md"