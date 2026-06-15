import hashlib
import json
from collections.abc import Mapping
from typing import Any


def calculate_content_checksum(content: str) -> str:
    """Calculate a deterministic checksum for document content."""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def calculate_metadata_checksum(metadata: Mapping[str, Any]) -> str:
    """Calculate a deterministic checksum for metadata.

    Metadata is serialized with sorted keys so equivalent dictionaries produce
    the same checksum regardless of insertion order.
    """

    serialized_metadata = json.dumps(
        metadata,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(serialized_metadata.encode("utf-8")).hexdigest()