from dataclasses import FrozenInstanceError
from datetime import datetime
from uuid import uuid4

import pytest

from app.domain.documents.entities import ChunkEmbeddingLink


def test_chunk_embedding_link_requires_timezone_aware_created_at() -> None:
    with pytest.raises(ValueError, match="created_at"):
        ChunkEmbeddingLink(
            id=uuid4(),
            chunk_version_id=uuid4(),
            embedding_record_id=uuid4(),
            created_at=datetime.now(),
        )


def test_chunk_embedding_link_is_immutable() -> None:
    link = ChunkEmbeddingLink(
        id=uuid4(),
        chunk_version_id=uuid4(),
        embedding_record_id=uuid4(),
    )

    with pytest.raises(FrozenInstanceError):
        link.embedding_record_id = uuid4()  # type: ignore[misc]