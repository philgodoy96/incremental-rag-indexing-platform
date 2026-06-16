from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from app.domain.documents.entities import EmbeddingCostRecord, EmbeddingRecord


def test_embedding_record_requires_vector_length_to_match_dimensions() -> None:
    with pytest.raises(ValueError, match="embedding_vector length"):
        EmbeddingRecord(
            id=uuid4(),
            chunk_version_id=uuid4(),
            provider="fake",
            model_name="fake-embedding-v1",
            embedding_input_hash="input-hash",
            embedding_vector=(0.1, 0.2),
            dimensions=3,
            input_token_estimate=10,
        )


def test_embedding_record_requires_positive_token_estimate() -> None:
    with pytest.raises(ValueError, match="input_token_estimate"):
        EmbeddingRecord(
            id=uuid4(),
            chunk_version_id=uuid4(),
            provider="fake",
            model_name="fake-embedding-v1",
            embedding_input_hash="input-hash",
            embedding_vector=(0.1,),
            dimensions=1,
            input_token_estimate=0,
        )


def test_embedding_record_is_immutable() -> None:
    record = EmbeddingRecord(
        id=uuid4(),
        chunk_version_id=uuid4(),
        provider="fake",
        model_name="fake-embedding-v1",
        embedding_input_hash="input-hash",
        embedding_vector=(0.1,),
        dimensions=1,
        input_token_estimate=10,
    )

    with pytest.raises(FrozenInstanceError):
        record.provider = "openai"  # type: ignore[misc]


def test_embedding_cost_record_rejects_negative_cost() -> None:
    with pytest.raises(ValueError, match="estimated_cost_usd_micros"):
        EmbeddingCostRecord(
            id=uuid4(),
            ingestion_run_id=uuid4(),
            embedding_record_id=uuid4(),
            provider="fake",
            model_name="fake-embedding-v1",
            input_token_estimate=10,
            estimated_cost_usd_micros=-1,
        )