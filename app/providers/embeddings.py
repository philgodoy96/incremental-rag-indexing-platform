from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class EmbeddingProviderResponse:
    provider: str
    model_name: str
    embedding_vector: tuple[float, ...]
    dimensions: int


class EmbeddingProvider(Protocol):
    provider: str
    model_name: str
    dimensions: int

    def embed(self, text: str) -> EmbeddingProviderResponse:
        raise NotImplementedError