from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.services.local_seed_document_discovery_service import (
    LocalSeedDocumentDiscoveryResult,
    LocalSeedDocumentDiscoveryService,
)
from app.config.settings import get_settings


class DiscoveredDocumentResponse(BaseModel):
    external_id: str
    source_uri: str
    title: str
    content_checksum: str
    metadata_checksum: str


class LocalSeedDocumentDiscoveryResponse(BaseModel):
    source_system: str
    source_path: str
    document_count: int
    documents: list[DiscoveredDocumentResponse]


router = APIRouter()


def get_local_seed_document_discovery_service() -> LocalSeedDocumentDiscoveryService:
    settings = get_settings()

    return LocalSeedDocumentDiscoveryService(
        source_path=Path(settings.seed_documents_path),
    )


@router.post(
    "/ingestion/local-seed-documents/discover",
    response_model=LocalSeedDocumentDiscoveryResponse,
)
def discover_local_seed_documents(
    service: Annotated[
        LocalSeedDocumentDiscoveryService,
        Depends(get_local_seed_document_discovery_service),
    ],
) -> LocalSeedDocumentDiscoveryResponse:
    """Discover local seed Markdown documents without persisting them."""

    result = service.discover()

    return build_discovery_response(result)


def build_discovery_response(
    result: LocalSeedDocumentDiscoveryResult,
) -> LocalSeedDocumentDiscoveryResponse:
    return LocalSeedDocumentDiscoveryResponse(
        source_system=result.source_system.value,
        source_path=result.source_path,
        document_count=result.document_count,
        documents=[
            DiscoveredDocumentResponse(
                external_id=document.external_id,
                source_uri=document.source_uri,
                title=document.title,
                content_checksum=document.content_checksum,
                metadata_checksum=document.metadata_checksum,
            )
            for document in result.documents
        ],
    )