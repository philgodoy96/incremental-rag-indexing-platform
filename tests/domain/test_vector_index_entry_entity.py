from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.documents.entities import VectorIndexEntry


def make_vector_index_entry() -> VectorIndexEntry:
    return VectorIndexEntry(
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


def test_vector_index_entry_requires_matching_vector_dimensions() -> None:
    with pytest.raises(ValueError, match="embedding_vector length"):
        VectorIndexEntry(
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
            embedding_vector=(0.1, 0.2),
            dimensions=3,
        )


def test_vector_index_entry_requires_timezone_aware_timestamps() -> None:
    with pytest.raises(ValueError, match="created_at"):
        VectorIndexEntry(
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
            created_at=datetime.now(),
        )


def test_vector_index_entry_can_update_current_projection() -> None:
    entry = make_vector_index_entry()

    new_document_version_id = uuid4()
    new_section_version_id = uuid4()
    new_chunk_version_id = uuid4()
    new_embedding_record_id = uuid4()
    updated_at = datetime.now(UTC)

    entry.update_current_projection(
        document_version_id=new_document_version_id,
        section_version_id=new_section_version_id,
        chunk_version_id=new_chunk_version_id,
        embedding_record_id=new_embedding_record_id,
        embedding_input_hash="new-embedding-input-hash",
        content="Status: At Risk",
        heading_context=("Project Atlas Status", "Summary"),
        embedding_vector=(0.4, 0.5, 0.6),
        dimensions=3,
        updated_at=updated_at,
    )

    assert entry.document_version_id == new_document_version_id
    assert entry.section_version_id == new_section_version_id
    assert entry.chunk_version_id == new_chunk_version_id
    assert entry.embedding_record_id == new_embedding_record_id
    assert entry.embedding_input_hash == "new-embedding-input-hash"
    assert entry.content == "Status: At Risk"
    assert entry.embedding_vector == (0.4, 0.5, 0.6)
    assert entry.dimensions == 3
    assert entry.is_active is True
    assert entry.updated_at == updated_at


def test_vector_index_entry_can_be_deactivated() -> None:
    entry = make_vector_index_entry()
    updated_at = datetime.now(UTC)

    entry.deactivate(updated_at=updated_at)

    assert entry.is_active is False
    assert entry.updated_at == updated_at