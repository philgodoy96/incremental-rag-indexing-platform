from app.application.services.source_document_discovery import (
    SourceDocumentDiscoveryResult,
    SourceDocumentDiscoveryService,
)
from app.domain.documents.enums import SourceSystem


class _DiscoveryServiceStub:
    def __init__(self, result: SourceDocumentDiscoveryResult) -> None:
        self._result = result

    def discover(self) -> SourceDocumentDiscoveryResult:
        return self._result


def test_source_document_discovery_service_protocol_is_structural() -> None:
    def accepts_discovery_service(service: SourceDocumentDiscoveryService) -> int:
        return service.discover().document_count

    result = SourceDocumentDiscoveryResult(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        source_path="seed_documents",
        documents=(),
    )

    assert accepts_discovery_service(_DiscoveryServiceStub(result)) == 0
