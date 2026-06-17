from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.retrieval.enums import QueryTraceStatus

MAX_RETRIEVAL_TOP_K = 20


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def ensure_timezone_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


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
    query_trace_id: UUID | None = None

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


@dataclass(slots=True)
class QueryTrace:
    id: UUID
    query: str
    provider: str
    model_name: str
    top_k: int
    status: QueryTraceStatus = QueryTraceStatus.STARTED
    started_at: datetime = field(default_factory=utc_now)
    query_embedding_dimensions: int | None = None
    results_count: int = 0
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        ensure_not_blank(self.query, "query")
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")
        ensure_timezone_aware(self.started_at, "started_at")

        if self.top_k < 1:
            raise ValueError("top_k must be greater than or equal to 1")

        if self.top_k > MAX_RETRIEVAL_TOP_K:
            raise ValueError(
                f"top_k must be less than or equal to {MAX_RETRIEVAL_TOP_K}",
            )

        if (
            self.query_embedding_dimensions is not None
            and self.query_embedding_dimensions < 1
        ):
            raise ValueError(
                "query_embedding_dimensions must be greater than or equal to 1",
            )

        if self.results_count < 0:
            raise ValueError("results_count must not be negative")

        if self.results_count > self.top_k:
            raise ValueError("results_count must not exceed top_k")

        if self.completed_at is not None:
            ensure_timezone_aware(self.completed_at, "completed_at")

        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("duration_ms must not be negative")

        if self.status == QueryTraceStatus.FAILED and not self.error_message:
            raise ValueError("failed query trace must include error_message")

    @classmethod
    def start(
        cls,
        *,
        query: str,
        provider: str,
        model_name: str,
        top_k: int,
    ) -> "QueryTrace":
        return cls(
            id=uuid4(),
            query=query,
            provider=provider,
            model_name=model_name,
            top_k=top_k,
        )

    def mark_completed(
        self,
        *,
        query_embedding_dimensions: int,
        results_count: int,
        completed_at: datetime | None = None,
    ) -> None:
        if query_embedding_dimensions < 1:
            raise ValueError(
                "query_embedding_dimensions must be greater than or equal to 1",
            )

        if results_count < 0:
            raise ValueError("results_count must not be negative")

        if results_count > self.top_k:
            raise ValueError("results_count must not exceed top_k")

        finished_at = completed_at or utc_now()
        ensure_timezone_aware(finished_at, "completed_at")

        duration_ms = int((finished_at - self.started_at).total_seconds() * 1000)

        if duration_ms < 0:
            raise ValueError("duration_ms must not be negative")

        self.status = QueryTraceStatus.COMPLETED
        self.query_embedding_dimensions = query_embedding_dimensions
        self.results_count = results_count
        self.completed_at = finished_at
        self.duration_ms = duration_ms
        self.error_message = None

    def mark_failed(
        self,
        *,
        error_message: str,
        completed_at: datetime | None = None,
    ) -> None:
        ensure_not_blank(error_message, "error_message")

        finished_at = completed_at or utc_now()
        ensure_timezone_aware(finished_at, "completed_at")

        duration_ms = int((finished_at - self.started_at).total_seconds() * 1000)

        if duration_ms < 0:
            raise ValueError("duration_ms must not be negative")

        self.status = QueryTraceStatus.FAILED
        self.completed_at = finished_at
        self.duration_ms = duration_ms
        self.error_message = error_message


@dataclass(frozen=True, slots=True)
class QueryTraceHit:
    id: UUID
    query_trace_id: UUID
    rank: int
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
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        ensure_not_blank(self.stable_section_key, "stable_section_key")
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")
        ensure_not_blank(self.content, "content")
        ensure_timezone_aware(self.created_at, "created_at")

        if self.rank < 1:
            raise ValueError("rank must be greater than or equal to 1")

        if self.chunk_index < 0:
            raise ValueError("chunk_index must not be negative")

        if not self.heading_context:
            raise ValueError("heading_context must not be empty")

        if self.distance < 0:
            raise ValueError("distance must not be negative")