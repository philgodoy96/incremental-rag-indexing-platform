from dataclasses import dataclass
from uuid import uuid4

from app.domain.documents.checksums import calculate_content_checksum
from app.domain.documents.entities import ChunkVersion, SectionVersion


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    target_chunk_words: int = 120
    max_chunk_words: int = 180
    overlap_words: int = 30

    def __post_init__(self) -> None:
        if self.target_chunk_words < 1:
            raise ValueError("target_chunk_words must be greater than or equal to 1")

        if self.max_chunk_words < self.target_chunk_words:
            raise ValueError("max_chunk_words must be greater than or equal to target")

        if self.overlap_words < 0:
            raise ValueError("overlap_words must not be negative")

        if self.overlap_words >= self.target_chunk_words:
            raise ValueError("overlap_words must be smaller than target_chunk_words")


class MarkdownChunkingService:
    """Creates deterministic chunks from section versions."""

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self._config = config or ChunkingConfig()

    def create_chunk_versions(
        self,
        *,
        section_version: SectionVersion,
    ) -> list[ChunkVersion]:
        chunk_texts = split_words_into_chunks(
            text=section_version.body,
            target_chunk_words=self._config.target_chunk_words,
            overlap_words=self._config.overlap_words,
        )

        return [
            ChunkVersion(
                id=uuid4(),
                section_version_id=section_version.id,
                chunk_index=index,
                content=chunk_text,
                heading_context=section_version.heading_path,
                chunk_hash=calculate_chunk_hash(chunk_text),
                embedding_input_hash=calculate_embedding_input_hash(
                    heading_context=section_version.heading_path,
                    content=chunk_text,
                ),
                token_estimate=estimate_tokens(chunk_text),
            )
            for index, chunk_text in enumerate(chunk_texts)
        ]


def split_words_into_chunks(
    *,
    text: str,
    target_chunk_words: int,
    overlap_words: int,
) -> list[str]:
    words = normalize_text_for_chunking(text).split()

    if not words:
        return []

    if len(words) <= target_chunk_words:
        return [" ".join(words)]

    chunks: list[str] = []
    step = target_chunk_words - overlap_words
    start = 0

    while start < len(words):
        end = min(start + target_chunk_words, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if end == len(words):
            break

        start += step

    return chunks


def normalize_text_for_chunking(text: str) -> str:
    return " ".join(text.split())


def calculate_chunk_hash(content: str) -> str:
    return calculate_content_checksum(content)


def calculate_embedding_input_hash(
    *,
    heading_context: tuple[str, ...],
    content: str,
) -> str:
    embedding_input = "\n".join([*heading_context, content])

    return calculate_content_checksum(embedding_input)


def estimate_tokens(content: str) -> int:
    return max(1, len(content.split()))