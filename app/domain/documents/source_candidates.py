from dataclasses import dataclass
from pathlib import PurePosixPath

from app.domain.documents.checksums import (
    calculate_content_checksum,
    calculate_metadata_checksum,
)
from app.domain.documents.entities import ensure_not_blank
from app.domain.documents.enums import SourceSystem


@dataclass(frozen=True, slots=True)
class SourceDocumentCandidate:
    """A source document discovered before persistence.

    This object represents a document found in a source system. It is not yet a
    SourceDocument because it has not been persisted and versioned.
    """

    source_system: SourceSystem
    external_id: str
    source_uri: str
    title: str
    raw_content: str
    content_checksum: str
    metadata_checksum: str
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ensure_not_blank(self.external_id, "external_id")
        ensure_not_blank(self.source_uri, "source_uri")
        ensure_not_blank(self.title, "title")
        ensure_not_blank(self.raw_content, "raw_content")
        ensure_not_blank(self.content_checksum, "content_checksum")
        ensure_not_blank(self.metadata_checksum, "metadata_checksum")

    @classmethod
    def create(
        cls,
        *,
        source_system: SourceSystem,
        external_id: str,
        source_uri: str,
        title: str,
        raw_content: str,
        tags: tuple[str, ...] = (),
    ) -> "SourceDocumentCandidate":
        normalized_external_id = normalize_external_id(external_id)
        normalized_source_uri = normalize_source_uri(source_uri)

        metadata: dict[str, object] = {
            "source_system": source_system.value,
            "external_id": normalized_external_id,
            "source_uri": normalized_source_uri,
            "title": title,
        }

        if tags:
            metadata["tags"] = list(tags)

        return cls(
            source_system=source_system,
            external_id=normalized_external_id,
            source_uri=normalized_source_uri,
            title=title,
            raw_content=raw_content,
            content_checksum=calculate_content_checksum(raw_content),
            metadata_checksum=calculate_metadata_checksum(metadata),
            tags=tags,
        )


def normalize_external_id(value: str) -> str:
    """Normalize a relative source path into a stable external id."""

    ensure_not_blank(value, "external_id")

    return PurePosixPath(value.replace("\\", "/")).as_posix()


def normalize_source_uri(value: str) -> str:
    """Normalize a source URI into a stable representation."""

    ensure_not_blank(value, "source_uri")

    normalized = value.replace("\\", "/")

    if "://" in normalized:
        scheme, _, remainder = normalized.partition("://")
        return f"{scheme}://{remainder.lstrip('/')}"

    return PurePosixPath(normalized).as_posix()