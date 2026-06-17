from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import (
    get_answering_transaction,
    get_grounded_answer_service,
)
from app.application.services.grounded_answer_service import GroundedAnswerService
from app.application.transactions.answering import AnsweringTransaction
from app.domain.answering.entities import GroundedAnswerRequest
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