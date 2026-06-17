from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.retrieval.entities import QueryTrace, QueryTraceHit
from app.domain.retrieval.enums import QueryTraceStatus


def test_query_trace_starts_with_started_status() -> None:
    trace = QueryTrace.start(
        query="What is Project Atlas status?",
        provider="fake",
        model_name="fake-embedding-v1",
        top_k=5,
    )

    assert trace.status == QueryTraceStatus.STARTED
    assert trace.results_count == 0
    assert trace.completed_at is None
    assert trace.duration_ms is None


def test_query_trace_can_be_marked_completed() -> None:
    started_at = datetime.now(UTC)

    trace = QueryTrace(
        id=uuid4(),
        query="What is Project Atlas status?",
        provider="fake",
        model_name="fake-embedding-v1",
        top_k=5,
        started_at=started_at,
    )

    trace.mark_completed(
        query_embedding_dimensions=8,
        results_count=2,
        completed_at=started_at + timedelta(milliseconds=125),
    )

    assert trace.status == QueryTraceStatus.COMPLETED
    assert trace.query_embedding_dimensions == 8
    assert trace.results_count == 2
    assert trace.duration_ms == 125
    assert trace.error_message is None


def test_query_trace_rejects_more_results_than_top_k() -> None:
    trace = QueryTrace.start(
        query="What is Project Atlas status?",
        provider="fake",
        model_name="fake-embedding-v1",
        top_k=1,
    )

    with pytest.raises(ValueError, match="results_count must not exceed top_k"):
        trace.mark_completed(
            query_embedding_dimensions=8,
            results_count=2,
        )


def test_query_trace_can_be_marked_failed() -> None:
    started_at = datetime.now(UTC)

    trace = QueryTrace(
        id=uuid4(),
        query="What is Project Atlas status?",
        provider="fake",
        model_name="fake-embedding-v1",
        top_k=5,
        started_at=started_at,
    )

    trace.mark_failed(
        error_message="embedding provider failed",
        completed_at=started_at + timedelta(milliseconds=50),
    )

    assert trace.status == QueryTraceStatus.FAILED
    assert trace.error_message == "embedding provider failed"
    assert trace.duration_ms == 50


def test_query_trace_hit_rejects_invalid_rank() -> None:
    with pytest.raises(ValueError, match="rank must be greater"):
        QueryTraceHit(
            id=uuid4(),
            query_trace_id=uuid4(),
            rank=0,
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
            distance=0.12,
        )


def test_query_trace_hit_requires_non_negative_distance() -> None:
    with pytest.raises(ValueError, match="distance must not be negative"):
        QueryTraceHit(
            id=uuid4(),
            query_trace_id=uuid4(),
            rank=1,
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
            distance=-0.01,
        )