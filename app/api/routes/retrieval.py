from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
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
    QueryTrace,
    QueryTraceHit,
    SemanticSearchQuery,
)
from app.domain.retrieval.enums import QueryTraceStatus

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
    query_trace_id: UUID
    query: str
    top_k: int
    provider: str
    model_name: str
    results: list[RetrievedChunkResponse]


class QueryTraceSummaryResponse(BaseModel):
    id: UUID
    query: str
    provider: str
    model_name: str
    top_k: int
    status: QueryTraceStatus
    query_embedding_dimensions: int | None
    results_count: int
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    error_message: str | None


class QueryTraceListResponse(BaseModel):
    items: list[QueryTraceSummaryResponse]
    limit: int
    offset: int


class QueryTraceHitResponse(BaseModel):
    id: UUID
    query_trace_id: UUID
    rank: int
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
    created_at: datetime


class QueryTraceDetailResponse(QueryTraceSummaryResponse):
    hits: list[QueryTraceHitResponse]


def _to_query_trace_summary_response(trace: QueryTrace) -> QueryTraceSummaryResponse:
    return QueryTraceSummaryResponse(
        id=trace.id,
        query=trace.query,
        provider=trace.provider,
        model_name=trace.model_name,
        top_k=trace.top_k,
        status=trace.status,
        query_embedding_dimensions=trace.query_embedding_dimensions,
        results_count=trace.results_count,
        started_at=trace.started_at,
        completed_at=trace.completed_at,
        duration_ms=trace.duration_ms,
        error_message=trace.error_message,
    )


def _to_query_trace_hit_response(hit: QueryTraceHit) -> QueryTraceHitResponse:
    return QueryTraceHitResponse(
        id=hit.id,
        query_trace_id=hit.query_trace_id,
        rank=hit.rank,
        vector_index_entry_id=hit.vector_index_entry_id,
        source_document_id=hit.source_document_id,
        document_version_id=hit.document_version_id,
        section_version_id=hit.section_version_id,
        chunk_version_id=hit.chunk_version_id,
        embedding_record_id=hit.embedding_record_id,
        stable_section_key=hit.stable_section_key,
        chunk_index=hit.chunk_index,
        provider=hit.provider,
        model_name=hit.model_name,
        content=hit.content,
        heading_context=list(hit.heading_context),
        distance=hit.distance,
        created_at=hit.created_at,
    )


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

    if result.query_trace_id is None:
        raise RuntimeError("query trace id is required")

    return SemanticSearchResponse(
        query_trace_id=result.query_trace_id,
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


@router.get("/traces", response_model=QueryTraceListResponse)
def list_query_traces(
    transaction: Annotated[
        RetrievalTransaction,
        Depends(get_retrieval_transaction),
    ],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: QueryTraceStatus | None = None,
    provider: str | None = Query(default=None, min_length=1),
    model_name: str | None = Query(default=None, min_length=1),
) -> QueryTraceListResponse:
    traces = transaction.query_traces.list_recent(
        limit=limit,
        offset=offset,
        status=status.value if status is not None else None,
        provider=provider,
        model_name=model_name,
    )

    return QueryTraceListResponse(
        items=[_to_query_trace_summary_response(trace) for trace in traces],
        limit=limit,
        offset=offset,
    )


@router.get("/traces/{trace_id}", response_model=QueryTraceDetailResponse)
def get_query_trace(
    trace_id: UUID,
    transaction: Annotated[
        RetrievalTransaction,
        Depends(get_retrieval_transaction),
    ],
) -> QueryTraceDetailResponse:
    trace = transaction.query_traces.get_by_id(trace_id)

    if trace is None:
        raise HTTPException(status_code=404, detail="Query trace not found")

    hits = transaction.query_trace_hits.list_by_trace_id(trace_id)

    summary = _to_query_trace_summary_response(trace)

    return QueryTraceDetailResponse(
        **summary.model_dump(),
        hits=[_to_query_trace_hit_response(hit) for hit in hits],
    )