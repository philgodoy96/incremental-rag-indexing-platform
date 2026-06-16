from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.documents.enums import (
    IngestionRunStatus,
    SourceDocumentStatus,
    SourceSystem,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def ensure_timezone_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(slots=True)
class SourceDocument:
    id: UUID
    source_system: SourceSystem
    external_id: str
    source_uri: str
    title: str
    status: SourceDocumentStatus = SourceDocumentStatus.ACTIVE
    current_document_version_id: UUID | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        ensure_not_blank(self.external_id, "external_id")
        ensure_not_blank(self.source_uri, "source_uri")
        ensure_not_blank(self.title, "title")
        ensure_timezone_aware(self.created_at, "created_at")
        ensure_timezone_aware(self.updated_at, "updated_at")

        if self.deleted_at is not None:
            ensure_timezone_aware(self.deleted_at, "deleted_at")

        if self.status == SourceDocumentStatus.DELETED and self.deleted_at is None:
            raise ValueError("deleted_at is required when source document is deleted")

    @classmethod
    def create(
        cls,
        *,
        source_system: SourceSystem,
        external_id: str,
        source_uri: str,
        title: str,
    ) -> "SourceDocument":
        now = utc_now()

        return cls(
            id=uuid4(),
            source_system=source_system,
            external_id=external_id,
            source_uri=source_uri,
            title=title,
            created_at=now,
            updated_at=now,
        )

    def refresh_metadata(
        self,
        *,
        source_uri: str,
        title: str,
        updated_at: datetime | None = None,
    ) -> None:
        ensure_not_blank(source_uri, "source_uri")
        ensure_not_blank(title, "title")

        self.source_uri = source_uri
        self.title = title
        self.updated_at = updated_at or utc_now()

    def mark_current_version(
        self,
        document_version_id: UUID,
        *,
        updated_at: datetime | None = None,
    ) -> None:
        self.current_document_version_id = document_version_id
        self.updated_at = updated_at or utc_now()

    def mark_deleted(self, *, deleted_at: datetime | None = None) -> None:
        deletion_time = deleted_at or utc_now()

        self.status = SourceDocumentStatus.DELETED
        self.deleted_at = deletion_time
        self.updated_at = deletion_time


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    id: UUID
    source_document_id: UUID
    version_number: int
    content_checksum: str
    metadata_checksum: str
    raw_content: str
    created_by_run_id: UUID
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.version_number < 1:
            raise ValueError("version_number must be greater than or equal to 1")

        ensure_not_blank(self.content_checksum, "content_checksum")
        ensure_not_blank(self.metadata_checksum, "metadata_checksum")
        ensure_not_blank(self.raw_content, "raw_content")
        ensure_timezone_aware(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class SectionVersion:
    id: UUID
    document_version_id: UUID
    stable_section_key: str
    heading_path: tuple[str, ...]
    heading_level: int
    title: str
    body: str
    section_checksum: str
    ordinal: int
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        ensure_not_blank(self.stable_section_key, "stable_section_key")
        ensure_not_blank(self.title, "title")
        ensure_not_blank(self.body, "body")
        ensure_not_blank(self.section_checksum, "section_checksum")
        ensure_timezone_aware(self.created_at, "created_at")

        if not self.heading_path:
            raise ValueError("heading_path must not be empty")

        if self.heading_level < 1 or self.heading_level > 6:
            raise ValueError("heading_level must be between 1 and 6")

        if self.ordinal < 0:
            raise ValueError("ordinal must not be negative")


@dataclass(frozen=True, slots=True)
class ChunkVersion:
    id: UUID
    section_version_id: UUID
    chunk_index: int
    content: str
    heading_context: tuple[str, ...]
    chunk_hash: str
    embedding_input_hash: str
    token_estimate: int
    risk_flags: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        ensure_not_blank(self.content, "content")
        ensure_not_blank(self.chunk_hash, "chunk_hash")
        ensure_not_blank(self.embedding_input_hash, "embedding_input_hash")
        ensure_timezone_aware(self.created_at, "created_at")

        if self.chunk_index < 0:
            raise ValueError("chunk_index must not be negative")

        if not self.heading_context:
            raise ValueError("heading_context must not be empty")

        if self.token_estimate < 1:
            raise ValueError("token_estimate must be greater than or equal to 1")

        for risk_flag in self.risk_flags:
            ensure_not_blank(risk_flag, "risk_flag")


@dataclass(slots=True)
class IngestionRun:
    id: UUID
    source_system: SourceSystem
    status: IngestionRunStatus
    started_at: datetime
    completed_at: datetime | None = None
    documents_seen: int = 0
    documents_changed: int = 0
    sections_created: int = 0
    chunks_created: int = 0
    error_message: str | None = None

    def __post_init__(self) -> None:
        ensure_timezone_aware(self.started_at, "started_at")

        if self.completed_at is not None:
            ensure_timezone_aware(self.completed_at, "completed_at")

        if self.documents_seen < 0:
            raise ValueError("documents_seen must not be negative")

        if self.documents_changed < 0:
            raise ValueError("documents_changed must not be negative")

        if self.sections_created < 0:
            raise ValueError("sections_created must not be negative")

        if self.chunks_created < 0:
            raise ValueError("chunks_created must not be negative")

        if self.documents_changed > self.documents_seen:
            raise ValueError("documents_changed cannot exceed documents_seen")

    @classmethod
    def start(cls, *, source_system: SourceSystem) -> "IngestionRun":
        return cls(
            id=uuid4(),
            source_system=source_system,
            status=IngestionRunStatus.RUNNING,
            started_at=utc_now(),
        )

    def mark_completed(
        self,
        *,
        documents_seen: int,
        documents_changed: int,
        sections_created: int = 0,
        chunks_created: int = 0,
        completed_at: datetime | None = None,
    ) -> None:
        completion_time = completed_at or utc_now()

        self.status = IngestionRunStatus.COMPLETED
        self.documents_seen = documents_seen
        self.documents_changed = documents_changed
        self.sections_created = sections_created
        self.chunks_created = chunks_created
        self.completed_at = completion_time

        self.__post_init__()

    def mark_failed(
        self,
        *,
        error_message: str,
        completed_at: datetime | None = None,
    ) -> None:
        ensure_not_blank(error_message, "error_message")

        self.status = IngestionRunStatus.FAILED
        self.error_message = error_message
        self.completed_at = completed_at or utc_now()

        self.__post_init__()