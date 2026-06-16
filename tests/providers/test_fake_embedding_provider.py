import pytest

from app.providers.fake_embedding_provider import FakeEmbeddingProvider


def test_fake_embedding_provider_is_deterministic() -> None:
    provider = FakeEmbeddingProvider()

    first = provider.embed("Project Atlas Status\nStatus: At Risk")
    second = provider.embed("Project Atlas Status\nStatus: At Risk")

    assert first == second
    assert first.provider == "fake"
    assert first.model_name == "fake-embedding-v1"
    assert first.dimensions == 8
    assert len(first.embedding_vector) == 8


def test_fake_embedding_provider_changes_vector_when_input_changes() -> None:
    provider = FakeEmbeddingProvider()

    first = provider.embed("Status: At Risk")
    second = provider.embed("Status: On Track")

    assert first.embedding_vector != second.embedding_vector


def test_fake_embedding_provider_rejects_blank_text() -> None:
    provider = FakeEmbeddingProvider()

    with pytest.raises(ValueError, match="text"):
        provider.embed("   ")