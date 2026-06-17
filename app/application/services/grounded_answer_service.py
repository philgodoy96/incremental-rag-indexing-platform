from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from app.application.transactions.answering import AnsweringTransaction
from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.answering.entities import (
    AnswerCitationRecord,
    AnswerRecord,
    GroundedAnswer,
    GroundedAnswerCitation,
    GroundedAnswerRequest,
)
from app.domain.llm_observability.entities import LLMProviderCallRecord
from app.domain.retrieval.entities import (
    SemanticSearchQuery,
    SemanticSearchResult,
)
from app.providers.llm import (
    LLMContextChunk,
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMProvider,
    LLMProviderError,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class SemanticRetriever(Protocol):
    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: RetrievalTransaction,
    ) -> SemanticSearchResult:
        raise NotImplementedError


class GroundedAnswerService:
    def __init__(
        self,
        *,
        retriever: SemanticRetriever,
        llm_provider: LLMProvider,
    ) -> None:
        self._retriever = retriever
        self._llm_provider = llm_provider

    def answer(
        self,
        *,
        request: GroundedAnswerRequest,
        transaction: AnsweringTransaction,
    ) -> GroundedAnswer:
        retrieval_result = self._retriever.search(
            query=SemanticSearchQuery(
                query=request.question,
                top_k=request.top_k,
                provider=request.provider,
                model_name=request.model_name,
            ),
            transaction=transaction,
        )

        if retrieval_result.query_trace_id is None:
            raise RuntimeError("query trace id is required")

        if not retrieval_result.results:
            grounded_answer = GroundedAnswer.insufficient_context(
                question=request.question,
                query_trace_id=retrieval_result.query_trace_id,
            )

            return self._persist_answer(
                grounded_answer=grounded_answer,
                request=request,
                transaction=transaction,
                llm_response=None,
                llm_started_at=None,
                llm_completed_at=None,
            )

        llm_started_at = utc_now()

        try:
            llm_response = self._llm_provider.generate_answer(
                LLMGenerationRequest(
                    question=request.question,
                    context_chunks=tuple(
                        LLMContextChunk(
                            rank=rank,
                            content=chunk.content,
                            heading_context=chunk.heading_context,
                        )
                        for rank, chunk in enumerate(
                            retrieval_result.results,
                            start=1,
                        )
                    ),
                ),
            )
        except LLMProviderError as error:
            llm_completed_at = utc_now()

            self._persist_failed_llm_provider_call(
                query_trace_id=retrieval_result.query_trace_id,
                transaction=transaction,
                error_message=str(error),
                started_at=llm_started_at,
                completed_at=llm_completed_at,
            )

            raise
        except Exception as error:
            llm_completed_at = utc_now()

            self._persist_failed_llm_provider_call(
                query_trace_id=retrieval_result.query_trace_id,
                transaction=transaction,
                error_message=(
                    f"unexpected provider error: "
                    f"{type(error).__name__}: {error}"
                ),
                started_at=llm_started_at,
                completed_at=llm_completed_at,
            )

            raise LLMProviderError("unexpected LLM provider error") from error

        llm_completed_at = utc_now()

        citations = tuple(
            GroundedAnswerCitation(
                rank=rank,
                vector_index_entry_id=chunk.vector_index_entry_id,
                source_document_id=chunk.source_document_id,
                document_version_id=chunk.document_version_id,
                section_version_id=chunk.section_version_id,
                chunk_version_id=chunk.chunk_version_id,
                embedding_record_id=chunk.embedding_record_id,
                stable_section_key=chunk.stable_section_key,
                chunk_index=chunk.chunk_index,
                heading_context=chunk.heading_context,
                quote=chunk.content,
                distance=chunk.distance,
            )
            for rank, chunk in enumerate(retrieval_result.results, start=1)
        )

        grounded_answer = GroundedAnswer.answered(
            question=request.question,
            answer=llm_response.answer,
            query_trace_id=retrieval_result.query_trace_id,
            citations=citations,
        )

        return self._persist_answer(
            grounded_answer=grounded_answer,
            request=request,
            transaction=transaction,
            llm_response=llm_response,
            llm_started_at=llm_started_at,
            llm_completed_at=llm_completed_at,
        )

    def _persist_answer(
        self,
        *,
        grounded_answer: GroundedAnswer,
        request: GroundedAnswerRequest,
        transaction: AnsweringTransaction,
        llm_response: LLMGenerationResponse | None,
        llm_started_at: datetime | None,
        llm_completed_at: datetime | None,
    ) -> GroundedAnswer:
        answer_record = AnswerRecord.from_grounded_answer(
            grounded_answer=grounded_answer,
            request=request,
        )

        citation_records = [
            AnswerCitationRecord.from_grounded_citation(
                answer_id=answer_record.id,
                citation=citation,
            )
            for citation in grounded_answer.citations
        ]

        llm_provider_call_record = None

        if llm_response is not None:
            if llm_started_at is None or llm_completed_at is None:
                raise RuntimeError("llm timing metadata is required")

            llm_provider_call_record = LLMProviderCallRecord.succeeded(
                answer_id=answer_record.id,
                query_trace_id=grounded_answer.query_trace_id,
                provider=llm_response.usage.provider,
                model_name=llm_response.usage.model_name,
                prompt_tokens=llm_response.usage.prompt_tokens,
                completion_tokens=llm_response.usage.completion_tokens,
                estimated_cost_usd=llm_response.usage.estimated_cost_usd,
                started_at=llm_started_at,
                completed_at=llm_completed_at,
            )

        transaction.answer_records.save(answer_record)
        transaction.flush()
        transaction.answer_citation_records.save_many(citation_records)

        if llm_provider_call_record is not None:
            transaction.llm_provider_calls.save(llm_provider_call_record)

        transaction.commit()

        return replace(grounded_answer, answer_id=answer_record.id)

    def _persist_failed_llm_provider_call(
        self,
        *,
        query_trace_id: UUID,
        transaction: AnsweringTransaction,
        error_message: str,
        started_at: datetime,
        completed_at: datetime,
    ) -> None:
        failed_provider_call = LLMProviderCallRecord.failed(
            answer_id=None,
            query_trace_id=query_trace_id,
            provider=self._llm_provider.provider,
            model_name=self._llm_provider.model_name,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at,
        )

        transaction.llm_provider_calls.save(failed_provider_call)
        transaction.commit()