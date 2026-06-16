import hashlib

from app.providers.embeddings import EmbeddingProviderResponse


class FakeEmbeddingProvider:
    """Deterministic fake embedding provider for local development and tests."""

    provider = "fake"
    model_name = "fake-embedding-v1"
    dimensions = 8

    def embed(self, text: str) -> EmbeddingProviderResponse:
        if not text.strip():
            raise ValueError("text must not be blank")

        digest = hashlib.sha256(
            f"{self.model_name}:{text}".encode(),
        ).digest()

        vector = tuple(
            normalize_uint16_to_unit_interval(
                int.from_bytes(
                    digest[(index * 2) % len(digest) : ((index * 2) % len(digest)) + 2],
                    byteorder="big",
                )
            )
            for index in range(self.dimensions)
        )

        return EmbeddingProviderResponse(
            provider=self.provider,
            model_name=self.model_name,
            embedding_vector=vector,
            dimensions=self.dimensions,
        )


def normalize_uint16_to_unit_interval(value: int) -> float:
    return round((value / 65535) * 2 - 1, 6)