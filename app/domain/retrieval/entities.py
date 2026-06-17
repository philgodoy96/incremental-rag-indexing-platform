from dataclasses import dataclass
from uuid import UUID

MAX_RETRIEVAL_TOP_K = 20


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class SemanticSearchQuery:
    query: str
    top_k: int
    provider: str
    model_name: str

    def __post_init__(self) -> None:
        ensure_not_blank(self.query, "query")
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")

        if self.top_k < 1:
            raise ValueError("top_k must be greater than or equal to 1")

        if self.top_k > MAX_RETRIEVAL_TOP_K:
            raise ValueError(
                f"top_k must be less than or equal to {MAX_RETRIEVAL_TOP_K}",
            )


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    vector_index_entry_id: UUID
    source_document_id: UUID
    document_version_id: UUID
    section_version_id: UUID
    chunk_version_id: UUID
    embedding_record_id: UUID
    stable_section_key: str
    chunk_index: int
    provider: str
    model_name: str
    content: str
    heading_context: tuple[str, ...]
    distance: float

    def __post_init__(self) -> None:
        ensure_not_blank(self.stable_section_key, "stable_section_key")
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")
        ensure_not_blank(self.content, "content")

        if self.chunk_index < 0:
            raise ValueError("chunk_index must not be negative")

        if not self.heading_context:
            raise ValueError("heading_context must not be empty")

        if self.distance < 0:
            raise ValueError("distance must not be negative")


@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    query: str
    top_k: int
    provider: str
    model_name: str
    results: tuple[RetrievedChunk, ...]

    def __post_init__(self) -> None:
        ensure_not_blank(self.query, "query")
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")

        if self.top_k < 1:
            raise ValueError("top_k must be greater than or equal to 1")

        if self.top_k > MAX_RETRIEVAL_TOP_K:
            raise ValueError(
                f"top_k must be less than or equal to {MAX_RETRIEVAL_TOP_K}",
            )

        if len(self.results) > self.top_k:
            raise ValueError("results length must not exceed top_k")