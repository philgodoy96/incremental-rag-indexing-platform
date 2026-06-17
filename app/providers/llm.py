from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


class LLMProviderError(Exception):
    def __init__(self, message: str) -> None:
        ensure_not_blank(message, "message")
        super().__init__(message)


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
class LLMUsageMetadata:
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: Decimal
    latency_ms: int

    def __post_init__(self) -> None:
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")

        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must not be negative")

        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must not be negative")

        if self.total_tokens < 0:
            raise ValueError("total_tokens must not be negative")

        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError(
                "total_tokens must equal prompt_tokens plus completion_tokens",
            )

        if self.estimated_cost_usd < Decimal("0"):
            raise ValueError("estimated_cost_usd must not be negative")

        if self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")


@dataclass(frozen=True, slots=True)
class LLMGenerationResponse:
    answer: str
    usage: LLMUsageMetadata

    def __post_init__(self) -> None:
        ensure_not_blank(self.answer, "answer")


class LLMProvider(Protocol):
    @property
    def provider(self) -> str:
        raise NotImplementedError

    @property
    def model_name(self) -> str:
        raise NotImplementedError

    def generate_answer(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        raise NotImplementedError