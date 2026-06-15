from app.domain.documents.checksums import (
    calculate_content_checksum,
    calculate_metadata_checksum,
)


def test_content_checksum_is_deterministic() -> None:
    content = "# Project Atlas\n\nStatus: On Track\n"

    first_checksum = calculate_content_checksum(content)
    second_checksum = calculate_content_checksum(content)

    assert first_checksum == second_checksum


def test_content_checksum_changes_when_content_changes() -> None:
    original = "# Project Atlas\n\nStatus: On Track\n"
    changed = "# Project Atlas\n\nStatus: At Risk\n"

    assert calculate_content_checksum(original) != calculate_content_checksum(changed)


def test_metadata_checksum_is_independent_of_key_order() -> None:
    first_metadata = {
        "source_system": "local_seed_documents",
        "external_id": "project-atlas-status.md",
        "title": "Project Atlas Status",
    }
    second_metadata = {
        "title": "Project Atlas Status",
        "external_id": "project-atlas-status.md",
        "source_system": "local_seed_documents",
    }

    assert calculate_metadata_checksum(first_metadata) == calculate_metadata_checksum(
        second_metadata
    )