from typing import Protocol

from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.answering.entities import (
    GroundedAnswer,
    GroundedAnswerCitation,
    GroundedAnswerRequest,
)
from app.domain.retrieval.entities import (
    SemanticSearchQuery,
    SemanticSearchResult,
)
from app.providers.llm import (
    LLMContextChunk,
    LLMGenerationRequest,
    LLMProvider,
)


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
        transaction: RetrievalTransaction,
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
            return GroundedAnswer.insufficient_context(
                question=request.question,
                query_trace_id=retrieval_result.query_trace_id,
            )

        llm_response = self._llm_provider.generate_answer(
            LLMGenerationRequest(
                question=request.question,
                context_chunks=tuple(
                    LLMContextChunk(
                        rank=rank,
                        content=chunk.content,
                        heading_context=chunk.heading_context,
                    )
                    for rank, chunk in enumerate(retrieval_result.results, start=1)
                ),
            ),
        )

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

        return GroundedAnswer.answered(
            question=request.question,
            answer=llm_response.answer,
            query_trace_id=retrieval_result.query_trace_id,
            citations=citations,
        )