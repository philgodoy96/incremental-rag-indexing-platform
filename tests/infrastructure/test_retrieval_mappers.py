from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.retrieval.entities import QueryTrace, QueryTraceHit
from app.domain.retrieval.enums import QueryTraceStatus
from app.infrastructure.db.mappers import (
    query_trace_from_model,
    query_trace_hit_from_model,
    query_trace_hit_to_model,
    query_trace_to_model,
)


def test_query_trace_mapper_round_trips_completed_entity() -> None:
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

    model = query_trace_to_model(trace)
    mapped_trace = query_trace_from_model(model)

    assert mapped_trace == trace
    assert mapped_trace.status == QueryTraceStatus.COMPLETED


def test_query_trace_hit_mapper_round_trips_entity() -> None:
    hit = QueryTraceHit(
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
        distance=0.12,
    )

    model = query_trace_hit_to_model(hit)
    mapped_hit = query_trace_hit_from_model(model)

    assert mapped_hit == hit