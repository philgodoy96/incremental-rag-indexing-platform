from app.domain.retrieval.entities import QueryTrace, QueryTraceHit
from app.domain.retrieval.enums import QueryTraceStatus
from app.infrastructure.db.models import QueryTraceHitModel, QueryTraceModel


def query_trace_to_model(entity: QueryTrace) -> QueryTraceModel:
    model = QueryTraceModel()

    model.id = entity.id
    model.query = entity.query
    model.provider = entity.provider
    model.model_name = entity.model_name
    model.top_k = entity.top_k
    model.status = entity.status.value
    model.query_embedding_dimensions = entity.query_embedding_dimensions
    model.results_count = entity.results_count
    model.started_at = entity.started_at
    model.completed_at = entity.completed_at
    model.duration_ms = entity.duration_ms
    model.error_message = entity.error_message

    return model


def query_trace_from_model(model: QueryTraceModel) -> QueryTrace:
    return QueryTrace(
        id=model.id,
        query=model.query,
        provider=model.provider,
        model_name=model.model_name,
        top_k=model.top_k,
        status=QueryTraceStatus(model.status),
        query_embedding_dimensions=model.query_embedding_dimensions,
        results_count=model.results_count,
        started_at=model.started_at,
        completed_at=model.completed_at,
        duration_ms=model.duration_ms,
        error_message=model.error_message,
    )


def query_trace_hit_to_model(entity: QueryTraceHit) -> QueryTraceHitModel:
    model = QueryTraceHitModel()

    model.id = entity.id
    model.query_trace_id = entity.query_trace_id
    model.rank = entity.rank
    model.vector_index_entry_id = entity.vector_index_entry_id
    model.source_document_id = entity.source_document_id
    model.document_version_id = entity.document_version_id
    model.section_version_id = entity.section_version_id
    model.chunk_version_id = entity.chunk_version_id
    model.embedding_record_id = entity.embedding_record_id
    model.stable_section_key = entity.stable_section_key
    model.chunk_index = entity.chunk_index
    model.provider = entity.provider
    model.model_name = entity.model_name
    model.content = entity.content
    model.heading_context = list(entity.heading_context)
    model.distance = entity.distance
    model.created_at = entity.created_at

    return model


def query_trace_hit_from_model(model: QueryTraceHitModel) -> QueryTraceHit:
    return QueryTraceHit(
        id=model.id,
        query_trace_id=model.query_trace_id,
        rank=model.rank,
        vector_index_entry_id=model.vector_index_entry_id,
        source_document_id=model.source_document_id,
        document_version_id=model.document_version_id,
        section_version_id=model.section_version_id,
        chunk_version_id=model.chunk_version_id,
        embedding_record_id=model.embedding_record_id,
        stable_section_key=model.stable_section_key,
        chunk_index=model.chunk_index,
        provider=model.provider,
        model_name=model.model_name,
        content=model.content,
        heading_context=tuple(model.heading_context),
        distance=model.distance,
        created_at=model.created_at,
    )