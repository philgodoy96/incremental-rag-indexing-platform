from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.dependencies import (
    get_answering_transaction,
    get_grounded_answer_service,
)
from app.application.services.grounded_answer_service import GroundedAnswerService
from app.application.transactions.answering import AnsweringTransaction
from app.domain.answering.entities import (
    AnswerCitationRecord,
    AnswerRecord,
    GroundedAnswerRequest,
)
from app.domain.answering.enums import GroundedAnswerStatus
from app.domain.retrieval.entities import MAX_RETRIEVAL_TOP_K

router = APIRouter(prefix="/answers", tags=["answers"])


class GroundedAnswerApiRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=MAX_RETRIEVAL_TOP_K)
    provider: str = Field(default="fake", min_length=1)
    model_name: str = Field(default="fake-embedding-v1", min_length=1)


class GroundedAnswerCitationResponse(BaseModel):
    rank: int
    vector_index_entry_id: UUID
    source_document_id: UUID
    document_version_id: UUID
    section_version_id: UUID
    chunk_version_id: UUID
    embedding_record_id: UUID
    stable_section_key: str
    chunk_index: int
    heading_context: list[str]
    quote: str
    distance: float


class GroundedAnswerApiResponse(BaseModel):
    answer_id: UUID
    question: str
    answer: str
    status: GroundedAnswerStatus
    query_trace_id: UUID
    citations: list[GroundedAnswerCitationResponse]


class AnswerSummaryResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    status: GroundedAnswerStatus
    query_trace_id: UUID
    top_k: int
    provider: str
    model_name: str
    created_at: datetime


class AnswerListResponse(BaseModel):
    items: list[AnswerSummaryResponse]
    limit: int
    offset: int


class AnswerCitationRecordResponse(BaseModel):
    id: UUID
    answer_id: UUID
    rank: int
    vector_index_entry_id: UUID
    source_document_id: UUID
    document_version_id: UUID
    section_version_id: UUID
    chunk_version_id: UUID
    embedding_record_id: UUID
    stable_section_key: str
    chunk_index: int
    heading_context: list[str]
    quote: str
    distance: float
    created_at: datetime


class AnswerDetailResponse(AnswerSummaryResponse):
    citations: list[AnswerCitationRecordResponse]


def _to_answer_summary_response(answer: AnswerRecord) -> AnswerSummaryResponse:
    return AnswerSummaryResponse(
        id=answer.id,
        question=answer.question,
        answer=answer.answer,
        status=answer.status,
        query_trace_id=answer.query_trace_id,
        top_k=answer.top_k,
        provider=answer.provider,
        model_name=answer.model_name,
        created_at=answer.created_at,
    )


def _to_answer_citation_record_response(
    citation: AnswerCitationRecord,
) -> AnswerCitationRecordResponse:
    return AnswerCitationRecordResponse(
        id=citation.id,
        answer_id=citation.answer_id,
        rank=citation.rank,
        vector_index_entry_id=citation.vector_index_entry_id,
        source_document_id=citation.source_document_id,
        document_version_id=citation.document_version_id,
        section_version_id=citation.section_version_id,
        chunk_version_id=citation.chunk_version_id,
        embedding_record_id=citation.embedding_record_id,
        stable_section_key=citation.stable_section_key,
        chunk_index=citation.chunk_index,
        heading_context=list(citation.heading_context),
        quote=citation.quote,
        distance=citation.distance,
        created_at=citation.created_at,
    )


@router.post("", response_model=GroundedAnswerApiResponse)
def create_grounded_answer(
    request: GroundedAnswerApiRequest,
    service: Annotated[
        GroundedAnswerService,
        Depends(get_grounded_answer_service),
    ],
    transaction: Annotated[
        AnsweringTransaction,
        Depends(get_answering_transaction),
    ],
) -> GroundedAnswerApiResponse:
    answer = service.answer(
        request=GroundedAnswerRequest(
            question=request.question,
            top_k=request.top_k,
            provider=request.provider,
            model_name=request.model_name,
        ),
        transaction=transaction,
    )

    if answer.answer_id is None:
        raise RuntimeError("answer id is required")

    return GroundedAnswerApiResponse(
        answer_id=answer.answer_id,
        question=answer.question,
        answer=answer.answer,
        status=answer.status,
        query_trace_id=answer.query_trace_id,
        citations=[
            GroundedAnswerCitationResponse(
                rank=citation.rank,
                vector_index_entry_id=citation.vector_index_entry_id,
                source_document_id=citation.source_document_id,
                document_version_id=citation.document_version_id,
                section_version_id=citation.section_version_id,
                chunk_version_id=citation.chunk_version_id,
                embedding_record_id=citation.embedding_record_id,
                stable_section_key=citation.stable_section_key,
                chunk_index=citation.chunk_index,
                heading_context=list(citation.heading_context),
                quote=citation.quote,
                distance=citation.distance,
            )
            for citation in answer.citations
        ],
    )


@router.get("", response_model=AnswerListResponse)
def list_answers(
    transaction: Annotated[
        AnsweringTransaction,
        Depends(get_answering_transaction),
    ],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: GroundedAnswerStatus | None = None,
    provider: str | None = Query(default=None, min_length=1),
    model_name: str | None = Query(default=None, min_length=1),
) -> AnswerListResponse:
    answers = transaction.answer_records.list_recent(
        limit=limit,
        offset=offset,
        status=status.value if status is not None else None,
        provider=provider,
        model_name=model_name,
    )

    return AnswerListResponse(
        items=[_to_answer_summary_response(answer) for answer in answers],
        limit=limit,
        offset=offset,
    )


@router.get("/{answer_id}", response_model=AnswerDetailResponse)
def get_answer(
    answer_id: UUID,
    transaction: Annotated[
        AnsweringTransaction,
        Depends(get_answering_transaction),
    ],
) -> AnswerDetailResponse:
    answer = transaction.answer_records.get_by_id(answer_id)

    if answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")

    citations = transaction.answer_citation_records.list_by_answer_id(answer_id)
    summary = _to_answer_summary_response(answer)

    return AnswerDetailResponse(
        **summary.model_dump(),
        citations=[
            _to_answer_citation_record_response(citation)
            for citation in citations
        ],
    )