from app.application.transactions.retrieval import RetrievalTransaction
from app.domain.retrieval.entities import (
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

        return SemanticSearchResult(
            query=query.query,
            top_k=query.top_k,
            provider=query.provider,
            model_name=query.model_name,
            results=tuple(retrieved_chunks),
        )