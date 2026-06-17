from dataclasses import dataclass
from uuid import UUID

from app.domain.answering.enums import GroundedAnswerStatus
from app.domain.retrieval.entities import MAX_RETRIEVAL_TOP_K


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class GroundedAnswerRequest:
    question: str
    top_k: int
    provider: str
    model_name: str

    def __post_init__(self) -> None:
        ensure_not_blank(self.question, "question")
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")

        if self.top_k < 1:
            raise ValueError("top_k must be greater than or equal to 1")

        if self.top_k > MAX_RETRIEVAL_TOP_K:
            raise ValueError(
                f"top_k must be less than or equal to {MAX_RETRIEVAL_TOP_K}",
            )


@dataclass(frozen=True, slots=True)
class GroundedAnswerCitation:
    rank: int
    vector_index_entry_id: UUID
    source_document_id: UUID
    document_version_id: UUID
    section_version_id: UUID
    chunk_version_id: UUID
    embedding_record_id: UUID
    stable_section_key: str
    chunk_index: int
    heading_context: tuple[str, ...]
    quote: str
    distance: float

    def __post_init__(self) -> None:
        ensure_not_blank(self.stable_section_key, "stable_section_key")
        ensure_not_blank(self.quote, "quote")

        if self.rank < 1:
            raise ValueError("rank must be greater than or equal to 1")

        if self.chunk_index < 0:
            raise ValueError("chunk_index must not be negative")

        if not self.heading_context:
            raise ValueError("heading_context must not be empty")

        if self.distance < 0:
            raise ValueError("distance must not be negative")


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    question: str
    answer: str
    status: GroundedAnswerStatus
    query_trace_id: UUID
    citations: tuple[GroundedAnswerCitation, ...]

    def __post_init__(self) -> None:
        ensure_not_blank(self.question, "question")

        if self.status == GroundedAnswerStatus.ANSWERED:
            ensure_not_blank(self.answer, "answer")

            if not self.citations:
                raise ValueError("answered grounded answer must include citations")

        if self.status == GroundedAnswerStatus.INSUFFICIENT_CONTEXT:
            ensure_not_blank(self.answer, "answer")

    @classmethod
    def answered(
        cls,
        *,
        question: str,
        answer: str,
        query_trace_id: UUID,
        citations: tuple[GroundedAnswerCitation, ...],
    ) -> "GroundedAnswer":
        return cls(
            question=question,
            answer=answer,
            status=GroundedAnswerStatus.ANSWERED,
            query_trace_id=query_trace_id,
            citations=citations,
        )

    @classmethod
    def insufficient_context(
        cls,
        *,
        question: str,
        query_trace_id: UUID,
    ) -> "GroundedAnswer":
        return cls(
            question=question,
            answer=(
                "I do not have enough retrieved context to answer this question "
                "reliably."
            ),
            status=GroundedAnswerStatus.INSUFFICIENT_CONTEXT,
            query_trace_id=query_trace_id,
            citations=(),
        )