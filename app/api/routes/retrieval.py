from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import (
    get_retrieval_transaction,
    get_semantic_retrieval_service,
)
from app.application.services.semantic_retrieval_service import (
    SemanticRetrievalService,
)
from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.retrieval.entities import (
    MAX_RETRIEVAL_TOP_K,
    SemanticSearchQuery,
)

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=MAX_RETRIEVAL_TOP_K)
    provider: str = Field(default="fake", min_length=1)
    model_name: str = Field(default="fake-embedding-v1", min_length=1)


class RetrievedChunkResponse(BaseModel):
    vector_index_entry_id: UUID
    source_document_id: UUID
    document_version_id: UUID
    section_version_id: UUID
    chunk_version_id: UUID
    embedding_record_id: UUID
    stable_section_key: str
    chunk_index: int
    provider: str
    model_name: str
    content: str
    heading_context: list[str]
    distance: float


class SemanticSearchResponse(BaseModel):
    query: str
    top_k: int
    provider: str
    model_name: str
    results: list[RetrievedChunkResponse]


@router.post("/search", response_model=SemanticSearchResponse)
def search_retrieval_index(
    request: SemanticSearchRequest,
    service: Annotated[
        SemanticRetrievalService,
        Depends(get_semantic_retrieval_service),
    ],
    transaction: Annotated[
        RetrievalTransaction,
        Depends(get_retrieval_transaction),
    ],
) -> SemanticSearchResponse:
    result = service.search(
        query=SemanticSearchQuery(
            query=request.query,
            top_k=request.top_k,
            provider=request.provider,
            model_name=request.model_name,
        ),
        transaction=transaction,
    )

    return SemanticSearchResponse(
        query=result.query,
        top_k=result.top_k,
        provider=result.provider,
        model_name=result.model_name,
        results=[
            RetrievedChunkResponse(
                vector_index_entry_id=chunk.vector_index_entry_id,
                source_document_id=chunk.source_document_id,
                document_version_id=chunk.document_version_id,
                section_version_id=chunk.section_version_id,
                chunk_version_id=chunk.chunk_version_id,
                embedding_record_id=chunk.embedding_record_id,
                stable_section_key=chunk.stable_section_key,
                chunk_index=chunk.chunk_index,
                provider=chunk.provider,
                model_name=chunk.model_name,
                content=chunk.content,
                heading_context=list(chunk.heading_context),
                distance=chunk.distance,
            )
            for chunk in result.results
        ],
    )