from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from app.domain.documents.entities import ChunkVersion


def test_chunk_version_requires_non_negative_chunk_index() -> None:
    with pytest.raises(ValueError, match="chunk_index"):
        ChunkVersion(
            id=uuid4(),
            section_version_id=uuid4(),
            chunk_index=-1,
            content="Status: At Risk",
            heading_context=("Project Atlas", "Summary"),
            chunk_hash="chunk-hash",
            embedding_input_hash="embedding-input-hash",
            token_estimate=3,
        )


def test_chunk_version_requires_heading_context() -> None:
    with pytest.raises(ValueError, match="heading_context"):
        ChunkVersion(
            id=uuid4(),
            section_version_id=uuid4(),
            chunk_index=0,
            content="Status: At Risk",
            heading_context=(),
            chunk_hash="chunk-hash",
            embedding_input_hash="embedding-input-hash",
            token_estimate=3,
        )


def test_chunk_version_is_immutable() -> None:
    chunk = ChunkVersion(
        id=uuid4(),
        section_version_id=uuid4(),
        chunk_index=0,
        content="Status: At Risk",
        heading_context=("Project Atlas", "Summary"),
        chunk_hash="chunk-hash",
        embedding_input_hash="embedding-input-hash",
        token_estimate=3,
    )

    with pytest.raises(FrozenInstanceError):
        chunk.content = "Changed"  # type: ignore[misc]