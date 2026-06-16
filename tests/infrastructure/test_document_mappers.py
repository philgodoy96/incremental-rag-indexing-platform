from uuid import uuid4

from app.domain.documents.entities import (
    ChunkVersion,
    DocumentVersion,
    IngestionRun,
    SectionVersion,
    SourceDocument,
)
from app.domain.documents.enums import IngestionRunStatus, SourceSystem
from app.infrastructure.db.mappers.document_mappers import (
    chunk_version_from_model,
    chunk_version_to_model,
    document_version_from_model,
    document_version_to_model,
    ingestion_run_from_model,
    ingestion_run_to_model,
    section_version_from_model,
    section_version_to_model,
    source_document_from_model,
    source_document_to_model,
)


def test_source_document_mapper_round_trips_domain_entity() -> None:
    document = SourceDocument.create(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
        external_id="project-atlas-status.md",
        source_uri="seed_documents/project-atlas-status.md",
        title="Project Atlas Status",
    )
    version_id = uuid4()
    document.mark_current_version(version_id)

    model = source_document_to_model(document)
    mapped_document = source_document_from_model(model)

    assert mapped_document == document


def test_document_version_mapper_round_trips_domain_entity() -> None:
    document_version = DocumentVersion(
        id=uuid4(),
        source_document_id=uuid4(),
        version_number=1,
        content_checksum="content-checksum",
        metadata_checksum="metadata-checksum",
        raw_content="# Project Atlas Status",
        created_by_run_id=uuid4(),
    )

    model = document_version_to_model(document_version)
    mapped_version = document_version_from_model(model)

    assert mapped_version == document_version


def test_section_version_mapper_round_trips_domain_entity() -> None:
    section_version = SectionVersion(
        id=uuid4(),
        document_version_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        heading_path=("Project Atlas Status", "Summary"),
        heading_level=2,
        title="Summary",
        body="Project Atlas is at risk.",
        section_checksum="section-checksum",
        ordinal=0,
    )

    model = section_version_to_model(section_version)
    mapped_section = section_version_from_model(model)

    assert mapped_section == section_version


def test_chunk_version_mapper_round_trips_domain_entity() -> None:
    chunk_version = ChunkVersion(
        id=uuid4(),
        section_version_id=uuid4(),
        chunk_index=0,
        content="Project Atlas is at risk.",
        heading_context=("Project Atlas Status", "Summary"),
        chunk_hash="chunk-hash",
        embedding_input_hash="embedding-input-hash",
        token_estimate=5,
        risk_flags=("possible_prompt_injection",),
    )

    model = chunk_version_to_model(chunk_version)
    mapped_chunk = chunk_version_from_model(model)

    assert mapped_chunk == chunk_version


def test_ingestion_run_mapper_round_trips_domain_entity() -> None:
    ingestion_run = IngestionRun.start(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
    )
    ingestion_run.mark_completed(
        documents_seen=3,
        documents_changed=2,
        sections_created=8,
        chunks_created=8,
    )

    model = ingestion_run_to_model(ingestion_run)
    mapped_run = ingestion_run_from_model(model)

    assert mapped_run == ingestion_run
    assert mapped_run.status == IngestionRunStatus.COMPLETED
    assert mapped_run.sections_created == 8
    assert mapped_run.chunks_created == 8