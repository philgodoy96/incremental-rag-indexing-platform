from uuid import uuid4

import pytest

from app.domain.retrieval.entities import (
    MAX_RETRIEVAL_TOP_K,
    RetrievedChunk,
    SemanticSearchQuery,
    SemanticSearchResult,
)


def make_retrieved_chunk(distance: float = 0.12) -> RetrievedChunk:
    return RetrievedChunk(
        vector_index_entry_id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        chunk_index=0,
        provider="fake",
        model_name="fake-embedding-v1",
        content="Status: At Risk",
        heading_context=("Project Atlas Status", "Summary"),
        distance=distance,
    )


def test_semantic_search_query_requires_non_blank_query() -> None:
    with pytest.raises(ValueError, match="query must not be blank"):
        SemanticSearchQuery(
            query=" ",
            top_k=5,
            provider="fake",
            model_name="fake-embedding-v1",
        )


def test_semantic_search_query_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be greater"):
        SemanticSearchQuery(
            query="What is Project Atlas status?",
            top_k=0,
            provider="fake",
            model_name="fake-embedding-v1",
        )

    with pytest.raises(ValueError, match="top_k must be less"):
        SemanticSearchQuery(
            query="What is Project Atlas status?",
            top_k=MAX_RETRIEVAL_TOP_K + 1,
            provider="fake",
            model_name="fake-embedding-v1",
        )


def test_retrieved_chunk_rejects_negative_distance() -> None:
    with pytest.raises(ValueError, match="distance must not be negative"):
        make_retrieved_chunk(distance=-0.1)


def test_semantic_search_result_preserves_ranked_results() -> None:
    first = make_retrieved_chunk(distance=0.05)
    second = make_retrieved_chunk(distance=0.25)

    result = SemanticSearchResult(
        query="What is Project Atlas status?",
        top_k=5,
        provider="fake",
        model_name="fake-embedding-v1",
        results=(first, second),
    )

    assert result.results[0].distance == 0.05
    assert result.results[1].distance == 0.25


def test_semantic_search_result_rejects_more_results_than_top_k() -> None:
    with pytest.raises(ValueError, match="results length must not exceed top_k"):
        SemanticSearchResult(
            query="What is Project Atlas status?",
            top_k=1,
            provider="fake",
            model_name="fake-embedding-v1",
            results=(
                make_retrieved_chunk(distance=0.05),
                make_retrieved_chunk(distance=0.25),
            ),
        )