from uuid import uuid4

from app.domain.documents.entities import (
    ChunkEmbeddingLink,
    ChunkVersion,
    DocumentVersion,
    EmbeddingCostRecord,
    EmbeddingRecord,
    IngestionRun,
    SectionVersion,
    SourceDocument,
    VectorIndexEntry,
)
from app.domain.documents.enums import IngestionRunStatus, SourceSystem
from app.infrastructure.db.mappers.document_mappers import (
    chunk_embedding_link_from_model,
    chunk_embedding_link_to_model,
    chunk_version_from_model,
    chunk_version_to_model,
    document_version_from_model,
    document_version_to_model,
    embedding_cost_record_from_model,
    embedding_cost_record_to_model,
    embedding_record_from_model,
    embedding_record_to_model,
    ingestion_run_from_model,
    ingestion_run_to_model,
    section_version_from_model,
    section_version_to_model,
    source_document_from_model,
    source_document_to_model,
    vector_index_entry_from_model,
    vector_index_entry_to_model,
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


def test_embedding_record_mapper_round_trips_domain_entity() -> None:
    embedding_record = EmbeddingRecord(
        id=uuid4(),
        chunk_version_id=uuid4(),
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash="embedding-input-hash",
        embedding_vector=(0.1, 0.2, 0.3),
        dimensions=3,
        input_token_estimate=12,
    )

    model = embedding_record_to_model(embedding_record)
    mapped_embedding = embedding_record_from_model(model)

    assert mapped_embedding == embedding_record


def test_chunk_embedding_link_mapper_round_trips_domain_entity() -> None:
    link = ChunkEmbeddingLink(
        id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
    )

    model = chunk_embedding_link_to_model(link)
    mapped_link = chunk_embedding_link_from_model(model)

    assert mapped_link == link


def test_vector_index_entry_mapper_round_trips_domain_entity() -> None:
    entry = VectorIndexEntry(
        id=uuid4(),
        source_document_id=uuid4(),
        document_version_id=uuid4(),
        section_version_id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        chunk_index=0,
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash="embedding-input-hash",
        content="Status: On Track",
        heading_context=("Project Atlas Status", "Summary"),
        embedding_vector=(0.1, 0.2, 0.3),
        dimensions=3,
    )

    model = vector_index_entry_to_model(entry)
    mapped_entry = vector_index_entry_from_model(model)

    assert mapped_entry == entry


def test_embedding_cost_record_mapper_round_trips_domain_entity() -> None:
    cost_record = EmbeddingCostRecord(
        id=uuid4(),
        ingestion_run_id=uuid4(),
        embedding_record_id=uuid4(),
        provider="fake",
        model_name="fake-embedding-v1",
        input_token_estimate=12,
        estimated_cost_usd_micros=0,
    )

    model = embedding_cost_record_to_model(cost_record)
    mapped_cost = embedding_cost_record_from_model(model)

    assert mapped_cost == cost_record


def test_ingestion_run_mapper_round_trips_domain_entity() -> None:
    ingestion_run = IngestionRun.start(
        source_system=SourceSystem.LOCAL_SEED_DOCUMENTS,
    )
    ingestion_run.mark_completed(
        documents_seen=3,
        documents_changed=2,
        sections_created=8,
        chunks_created=8,
        embeddings_created=6,
        embeddings_reused=2,
        vector_entries_created=4,
        vector_entries_updated=2,
        vector_entries_deactivated=1,
        embedding_tokens_processed=300,
        estimated_embedding_cost_usd_micros=0,
    )

    model = ingestion_run_to_model(ingestion_run)
    mapped_run = ingestion_run_from_model(model)

    assert mapped_run == ingestion_run
    assert mapped_run.status == IngestionRunStatus.COMPLETED
    assert mapped_run.embeddings_created == 6
    assert mapped_run.embeddings_reused == 2
    assert mapped_run.vector_entries_created == 4
    assert mapped_run.vector_entries_updated == 2
    assert mapped_run.vector_entries_deactivated == 1
    assert mapped_run.embedding_tokens_processed == 300