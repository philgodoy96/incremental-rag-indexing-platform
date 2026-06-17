from app.domain.answering.entities import AnswerCitationRecord, AnswerRecord
from app.domain.answering.enums import GroundedAnswerStatus
from app.infrastructure.db.models import (
    AnswerCitationRecordModel,
    AnswerRecordModel,
)


def answer_record_to_model(entity: AnswerRecord) -> AnswerRecordModel:
    model = AnswerRecordModel()

    model.id = entity.id
    model.question = entity.question
    model.answer = entity.answer
    model.status = entity.status.value
    model.query_trace_id = entity.query_trace_id
    model.top_k = entity.top_k
    model.provider = entity.provider
    model.model_name = entity.model_name
    model.created_at = entity.created_at

    return model


def answer_record_from_model(model: AnswerRecordModel) -> AnswerRecord:
    return AnswerRecord(
        id=model.id,
        question=model.question,
        answer=model.answer,
        status=GroundedAnswerStatus(model.status),
        query_trace_id=model.query_trace_id,
        top_k=model.top_k,
        provider=model.provider,
        model_name=model.model_name,
        created_at=model.created_at,
    )


def answer_citation_record_to_model(
    entity: AnswerCitationRecord,
) -> AnswerCitationRecordModel:
    model = AnswerCitationRecordModel()

    model.id = entity.id
    model.answer_id = entity.answer_id
    model.rank = entity.rank
    model.vector_index_entry_id = entity.vector_index_entry_id
    model.source_document_id = entity.source_document_id
    model.document_version_id = entity.document_version_id
    model.section_version_id = entity.section_version_id
    model.chunk_version_id = entity.chunk_version_id
    model.embedding_record_id = entity.embedding_record_id
    model.stable_section_key = entity.stable_section_key
    model.chunk_index = entity.chunk_index
    model.heading_context = list(entity.heading_context)
    model.quote = entity.quote
    model.distance = entity.distance
    model.created_at = entity.created_at

    return model


def answer_citation_record_from_model(
    model: AnswerCitationRecordModel,
) -> AnswerCitationRecord:
    return AnswerCitationRecord(
        id=model.id,
        answer_id=model.answer_id,
        rank=model.rank,
        vector_index_entry_id=model.vector_index_entry_id,
        source_document_id=model.source_document_id,
        document_version_id=model.document_version_id,
        section_version_id=model.section_version_id,
        chunk_version_id=model.chunk_version_id,
        embedding_record_id=model.embedding_record_id,
        stable_section_key=model.stable_section_key,
        chunk_index=model.chunk_index,
        heading_context=tuple(model.heading_context),
        quote=model.quote,
        distance=model.distance,
        created_at=model.created_at,
    )