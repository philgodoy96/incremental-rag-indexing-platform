from dataclasses import dataclass
from typing import Protocol


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class LLMContextChunk:
    rank: int
    content: str
    heading_context: tuple[str, ...]

    def __post_init__(self) -> None:
        ensure_not_blank(self.content, "content")

        if self.rank < 1:
            raise ValueError("rank must be greater than or equal to 1")

        if not self.heading_context:
            raise ValueError("heading_context must not be empty")


@dataclass(frozen=True, slots=True)
class LLMGenerationRequest:
    question: str
    context_chunks: tuple[LLMContextChunk, ...]

    def __post_init__(self) -> None:
        ensure_not_blank(self.question, "question")

        if not self.context_chunks:
            raise ValueError("context_chunks must not be empty")


@dataclass(frozen=True, slots=True)
class LLMGenerationResponse:
    answer: str

    def __post_init__(self) -> None:
        ensure_not_blank(self.answer, "answer")


class LLMProvider(Protocol):
    def generate_answer(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        raise NotImplementedError