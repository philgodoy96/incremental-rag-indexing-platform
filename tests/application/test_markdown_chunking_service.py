from uuid import uuid4

import pytest

from app.application.services.markdown_chunking_service import (
    ChunkingConfig,
    MarkdownChunkingService,
    calculate_embedding_input_hash,
    split_words_into_chunks,
)
from app.domain.documents.entities import SectionVersion


def make_section(body: str) -> SectionVersion:
    return SectionVersion(
        id=uuid4(),
        document_version_id=uuid4(),
        stable_section_key="project-atlas-status/summary",
        heading_path=("Project Atlas Status", "Summary"),
        heading_level=2,
        title="Summary",
        body=body,
        section_checksum="section-checksum",
        ordinal=0,
    )


def test_chunking_config_rejects_overlap_greater_than_target() -> None:
    with pytest.raises(ValueError, match="overlap_words"):
        ChunkingConfig(
            target_chunk_words=10,
            max_chunk_words=20,
            overlap_words=10,
        )


def test_split_words_into_chunks_is_deterministic() -> None:
    text = "one two three four five six seven eight nine ten"

    first = split_words_into_chunks(
        text=text,
        target_chunk_words=4,
        overlap_words=1,
    )
    second = split_words_into_chunks(
        text=text,
        target_chunk_words=4,
        overlap_words=1,
    )

    assert first == second
    assert first == [
        "one two three four",
        "four five six seven",
        "seven eight nine ten",
    ]


def test_markdown_chunking_service_creates_single_chunk_for_short_section() -> None:
    section = make_section("Project Atlas is currently at risk.")

    service = MarkdownChunkingService(
        config=ChunkingConfig(
            target_chunk_words=20,
            max_chunk_words=30,
            overlap_words=5,
        )
    )

    chunks = service.create_chunk_versions(section_version=section)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].heading_context == ("Project Atlas Status", "Summary")
    assert chunks[0].token_estimate == 6


def test_markdown_chunking_service_creates_overlapping_chunks() -> None:
    section = make_section("one two three four five six seven eight nine ten")

    service = MarkdownChunkingService(
        config=ChunkingConfig(
            target_chunk_words=4,
            max_chunk_words=6,
            overlap_words=1,
        )
    )

    chunks = service.create_chunk_versions(section_version=section)

    assert [chunk.content for chunk in chunks] == [
        "one two three four",
        "four five six seven",
        "seven eight nine ten",
    ]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]


def test_embedding_input_hash_includes_heading_context() -> None:
    content = "Status: At Risk"

    first_hash = calculate_embedding_input_hash(
        heading_context=("Project Atlas", "Summary"),
        content=content,
    )
    second_hash = calculate_embedding_input_hash(
        heading_context=("Project Atlas", "Risks"),
        content=content,
    )

    assert first_hash != second_hash