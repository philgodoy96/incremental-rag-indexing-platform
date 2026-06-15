from app.domain.documents.entities import DocumentVersion, IngestionRun, SourceDocument
from app.domain.documents.enums import (
    IngestionRunStatus,
    SourceDocumentStatus,
    SourceSystem,
)
from app.infrastructure.db.models.document_models import (
    DocumentVersionModel,
    IngestionRunModel,
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


def ingestion_run_to_model(entity: IngestionRun) -> IngestionRunModel:
    model = IngestionRunModel()

    model.id = entity.id
    model.source_system = entity.source_system.value
    model.status = entity.status.value
    model.started_at = entity.started_at
    model.completed_at = entity.completed_at
    model.documents_seen = entity.documents_seen
    model.documents_changed = entity.documents_changed
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
        error_message=model.error_message,
    )