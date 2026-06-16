from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.services.local_seed_document_discovery_service import (
    LocalSeedDocumentDiscoveryResult,
    LocalSeedDocumentDiscoveryService,
)
from app.application.services.local_seed_document_ingestion_service import (
    LocalSeedDocumentIngestionResult,
    LocalSeedDocumentIngestionService,
)
from app.config.settings import get_settings
from app.infrastructure.db.session import get_database_session
from app.infrastructure.transactions import SqlAlchemyDocumentIngestionTransaction


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


class IngestedDocumentResponse(BaseModel):
    external_id: str
    title: str
    action: str
    source_document_id: UUID
    document_version_id: UUID | None
    version_number: int | None
    content_checksum: str
    sections_created: int
    chunks_created: int
    embeddings_created: int
    embeddings_reused: int
    embedding_tokens_processed: int
    estimated_embedding_cost_usd_micros: int


class LocalSeedDocumentIngestionResponse(BaseModel):
    run_id: UUID
    source_system: str
    source_path: str
    status: str
    documents_seen: int
    documents_changed: int
    sections_created: int
    chunks_created: int
    embeddings_created: int
    embeddings_reused: int
    embedding_tokens_processed: int
    estimated_embedding_cost_usd_micros: int
    documents: list[IngestedDocumentResponse]


router = APIRouter()


def get_local_seed_document_discovery_service() -> LocalSeedDocumentDiscoveryService:
    settings = get_settings()

    return LocalSeedDocumentDiscoveryService(
        source_path=Path(settings.seed_documents_path),
    )


def get_local_seed_document_ingestion_service() -> LocalSeedDocumentIngestionService:
    settings = get_settings()

    return LocalSeedDocumentIngestionService(
        source_path=Path(settings.seed_documents_path),
    )


def get_document_ingestion_transaction(
    session: Annotated[Session, Depends(get_database_session)],
) -> SqlAlchemyDocumentIngestionTransaction:
    return SqlAlchemyDocumentIngestionTransaction(session=session)


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


@router.post(
    "/ingestion/local-seed-documents/runs",
    response_model=LocalSeedDocumentIngestionResponse,
)
def ingest_local_seed_documents(
    service: Annotated[
        LocalSeedDocumentIngestionService,
        Depends(get_local_seed_document_ingestion_service),
    ],
    transaction: Annotated[
        SqlAlchemyDocumentIngestionTransaction,
        Depends(get_document_ingestion_transaction),
    ],
) -> LocalSeedDocumentIngestionResponse:
    """Persist local seed Markdown documents as versioned source documents."""

    result = service.ingest(transaction)

    return build_ingestion_response(result)


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


def build_ingestion_response(
    result: LocalSeedDocumentIngestionResult,
) -> LocalSeedDocumentIngestionResponse:
    return LocalSeedDocumentIngestionResponse(
        run_id=result.run_id,
        source_system=result.source_system.value,
        source_path=result.source_path,
        status=result.status.value,
        documents_seen=result.documents_seen,
        documents_changed=result.documents_changed,
        sections_created=result.sections_created,
        chunks_created=result.chunks_created,
        embeddings_created=result.embeddings_created,
        embeddings_reused=result.embeddings_reused,
        embedding_tokens_processed=result.embedding_tokens_processed,
        estimated_embedding_cost_usd_micros=result.estimated_embedding_cost_usd_micros,
        documents=[
            IngestedDocumentResponse(
                external_id=document.external_id,
                title=document.title,
                action=document.action.value,
                source_document_id=document.source_document_id,
                document_version_id=document.document_version_id,
                version_number=document.version_number,
                content_checksum=document.content_checksum,
                sections_created=document.sections_created,
                chunks_created=document.chunks_created,
                embeddings_created=document.embeddings_created,
                embeddings_reused=document.embeddings_reused,
                embedding_tokens_processed=document.embedding_tokens_processed,
                estimated_embedding_cost_usd_micros=(
                    document.estimated_embedding_cost_usd_micros
                ),
            )
            for document in result.documents
        ],
    )