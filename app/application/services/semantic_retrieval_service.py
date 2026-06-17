from uuid import uuid4

from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.retrieval.entities import (
    QueryTrace,
    QueryTraceHit,
    SemanticSearchQuery,
    SemanticSearchResult,
)
from app.providers.embeddings import EmbeddingProvider


class SemanticRetrievalService:
    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider

    def search(
        self,
        *,
        query: SemanticSearchQuery,
        transaction: RetrievalTransaction,
    ) -> SemanticSearchResult:
        trace = QueryTrace.start(
            query=query.query,
            provider=query.provider,
            model_name=query.model_name,
            top_k=query.top_k,
        )
        transaction.query_traces.save(trace)
        transaction.flush()

        embedding_response = self._provider.embed(query.query)
        query_vector = tuple(embedding_response.embedding_vector)

        if not query_vector:
            raise ValueError("query embedding vector must not be empty")

        retrieved_chunks = transaction.vector_index_entries.search_active_by_vector(
            query_vector=query_vector,
            provider=query.provider,
            model_name=query.model_name,
            top_k=query.top_k,
        )

        trace_hits = [
            QueryTraceHit(
                id=uuid4(),
                query_trace_id=trace.id,
                rank=rank,
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
                heading_context=chunk.heading_context,
                distance=chunk.distance,
            )
            for rank, chunk in enumerate(retrieved_chunks, start=1)
        ]

        transaction.query_trace_hits.save_many(trace_hits)

        trace.mark_completed(
            query_embedding_dimensions=len(query_vector),
            results_count=len(retrieved_chunks),
        )
        transaction.query_traces.save(trace)
        transaction.commit()

        return SemanticSearchResult(
            query=query.query,
            top_k=query.top_k,
            provider=query.provider,
            model_name=query.model_name,
            results=tuple(retrieved_chunks),
            query_trace_id=trace.id,
        )
