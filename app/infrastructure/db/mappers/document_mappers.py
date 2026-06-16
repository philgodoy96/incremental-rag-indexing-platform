from app.domain.documents.entities import (
    ChunkVersion,
    DocumentVersion,
    EmbeddingCostRecord,
    EmbeddingRecord,
    IngestionRun,
    SectionVersion,
    SourceDocument,
)
from app.domain.documents.enums import (
    IngestionRunStatus,
    SourceDocumentStatus,
    SourceSystem,
)
from app.infrastructure.db.models.document_models import (
    ChunkVersionModel,
    DocumentVersionModel,
    EmbeddingCostRecordModel,
    EmbeddingRecordModel,
    IngestionRunModel,
    SectionVersionModel,
    SourceDocumentModel,
)


def source_document_to_model(entity: SourceDocument) -> SourceDocumentModel:
    model = SourceDocumentModel()

    model.id = entity.id
    model.source_system = entity.source_system.value
    model.external_id = entity.external_id
    model.source_uri = entity.source_uri
    model.title = entity.title
    model.status = entity.status.value
    model.current_document_version_id = entity.current_document_version_id
    model.created_at = entity.created_at
    model.updated_at = entity.updated_at
    model.deleted_at = entity.deleted_at

    return model


def source_document_from_model(model: SourceDocumentModel) -> SourceDocument:
    return SourceDocument(
        id=model.id,
        source_system=SourceSystem(model.source_system),
        external_id=model.external_id,
        source_uri=model.source_uri,
        title=model.title,
        status=SourceDocumentStatus(model.status),
        current_document_version_id=model.current_document_version_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def document_version_to_model(entity: DocumentVersion) -> DocumentVersionModel:
    model = DocumentVersionModel()

    model.id = entity.id
    model.source_document_id = entity.source_document_id
    model.version_number = entity.version_number
    model.content_checksum = entity.content_checksum
    model.metadata_checksum = entity.metadata_checksum
    model.raw_content = entity.raw_content
    model.created_by_run_id = entity.created_by_run_id
    model.created_at = entity.created_at

    return model


def document_version_from_model(model: DocumentVersionModel) -> DocumentVersion:
    return DocumentVersion(
        id=model.id,
        source_document_id=model.source_document_id,
        version_number=model.version_number,
        content_checksum=model.content_checksum,
        metadata_checksum=model.metadata_checksum,
        raw_content=model.raw_content,
        created_by_run_id=model.created_by_run_id,
        created_at=model.created_at,
    )


def section_version_to_model(entity: SectionVersion) -> SectionVersionModel:
    model = SectionVersionModel()

    model.id = entity.id
    model.document_version_id = entity.document_version_id
    model.stable_section_key = entity.stable_section_key
    model.heading_path = list(entity.heading_path)
    model.heading_level = entity.heading_level
    model.title = entity.title
    model.body = entity.body
    model.section_checksum = entity.section_checksum
    model.ordinal = entity.ordinal
    model.created_at = entity.created_at

    return model


def section_version_from_model(model: SectionVersionModel) -> SectionVersion:
    return SectionVersion(
        id=model.id,
        document_version_id=model.document_version_id,
        stable_section_key=model.stable_section_key,
        heading_path=tuple(model.heading_path),
        heading_level=model.heading_level,
        title=model.title,
        body=model.body,
        section_checksum=model.section_checksum,
        ordinal=model.ordinal,
        created_at=model.created_at,
    )


def chunk_version_to_model(entity: ChunkVersion) -> ChunkVersionModel:
    model = ChunkVersionModel()

    model.id = entity.id
    model.section_version_id = entity.section_version_id
    model.chunk_index = entity.chunk_index
    model.content = entity.content
    model.heading_context = list(entity.heading_context)
    model.chunk_hash = entity.chunk_hash
    model.embedding_input_hash = entity.embedding_input_hash
    model.token_estimate = entity.token_estimate
    model.risk_flags = list(entity.risk_flags)
    model.created_at = entity.created_at

    return model


def chunk_version_from_model(model: ChunkVersionModel) -> ChunkVersion:
    return ChunkVersion(
        id=model.id,
        section_version_id=model.section_version_id,
        chunk_index=model.chunk_index,
        content=model.content,
        heading_context=tuple(model.heading_context),
        chunk_hash=model.chunk_hash,
        embedding_input_hash=model.embedding_input_hash,
        token_estimate=model.token_estimate,
        risk_flags=tuple(model.risk_flags),
        created_at=model.created_at,
    )


def embedding_record_to_model(entity: EmbeddingRecord) -> EmbeddingRecordModel:
    model = EmbeddingRecordModel()

    model.id = entity.id
    model.chunk_version_id = entity.chunk_version_id
    model.provider = entity.provider
    model.model_name = entity.model_name
    model.embedding_input_hash = entity.embedding_input_hash
    model.embedding_vector = list(entity.embedding_vector)
    model.dimensions = entity.dimensions
    model.input_token_estimate = entity.input_token_estimate
    model.created_at = entity.created_at

    return model


def embedding_record_from_model(model: EmbeddingRecordModel) -> EmbeddingRecord:
    return EmbeddingRecord(
        id=model.id,
        chunk_version_id=model.chunk_version_id,
        provider=model.provider,
        model_name=model.model_name,
        embedding_input_hash=model.embedding_input_hash,
        embedding_vector=tuple(model.embedding_vector),
        dimensions=model.dimensions,
        input_token_estimate=model.input_token_estimate,
        created_at=model.created_at,
    )


def embedding_cost_record_to_model(
    entity: EmbeddingCostRecord,
) -> EmbeddingCostRecordModel:
    model = EmbeddingCostRecordModel()

    model.id = entity.id
    model.ingestion_run_id = entity.ingestion_run_id
    model.embedding_record_id = entity.embedding_record_id
    model.provider = entity.provider
    model.model_name = entity.model_name
    model.input_token_estimate = entity.input_token_estimate
    model.estimated_cost_usd_micros = entity.estimated_cost_usd_micros
    model.created_at = entity.created_at

    return model


def embedding_cost_record_from_model(
    model: EmbeddingCostRecordModel,
) -> EmbeddingCostRecord:
    return EmbeddingCostRecord(
        id=model.id,
        ingestion_run_id=model.ingestion_run_id,
        embedding_record_id=model.embedding_record_id,
        provider=model.provider,
        model_name=model.model_name,
        input_token_estimate=model.input_token_estimate,
        estimated_cost_usd_micros=model.estimated_cost_usd_micros,
        created_at=model.created_at,
    )


def ingestion_run_to_model(entity: IngestionRun) -> IngestionRunModel:
    model = IngestionRunModel()

    model.id = entity.id
    model.source_system = entity.source_system.value
    model.status = entity.status.value
    model.started_at = entity.started_at
    model.completed_at = entity.completed_at
    model.documents_seen = entity.documents_seen
    model.documents_changed = entity.documents_changed
    model.sections_created = entity.sections_created
    model.chunks_created = entity.chunks_created
    model.embeddings_created = entity.embeddings_created
    model.embedding_tokens_processed = entity.embedding_tokens_processed
    model.estimated_embedding_cost_usd_micros = (
        entity.estimated_embedding_cost_usd_micros
    )
    model.error_message = entity.error_message

    return model


def ingestion_run_from_model(model: IngestionRunModel) -> IngestionRun:
    return IngestionRun(
        id=model.id,
        source_system=SourceSystem(model.source_system),
        status=IngestionRunStatus(model.status),
        started_at=model.started_at,
        completed_at=model.completed_at,
        documents_seen=model.documents_seen,
        documents_changed=model.documents_changed,
        sections_created=model.sections_created,
        chunks_created=model.chunks_created,
        embeddings_created=model.embeddings_created,
        embedding_tokens_processed=model.embedding_tokens_processed,
        estimated_embedding_cost_usd_micros=model.estimated_embedding_cost_usd_micros,
        error_message=model.error_message,
    )