from dataclasses import dataclass
from decimal import Decimal


def ensure_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class LLMUsageSummary:
    call_count: int
    succeeded_count: int
    failed_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: Decimal
    average_latency_ms: float

    def __post_init__(self) -> None:
        if self.call_count < 0:
            raise ValueError("call_count must not be negative")

        if self.succeeded_count < 0:
            raise ValueError("succeeded_count must not be negative")

        if self.failed_count < 0:
            raise ValueError("failed_count must not be negative")

        if self.call_count != self.succeeded_count + self.failed_count:
            raise ValueError(
                "call_count must equal succeeded_count plus failed_count",
            )

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

        if self.average_latency_ms < 0:
            raise ValueError("average_latency_ms must not be negative")

    @classmethod
    def empty(cls) -> "LLMUsageSummary":
        return cls(
            call_count=0,
            succeeded_count=0,
            failed_count=0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost_usd=Decimal("0"),
            average_latency_ms=0.0,
        )


@dataclass(frozen=True, slots=True)
class LLMUsageByModelSummary:
    provider: str
    model_name: str
    call_count: int
    succeeded_count: int
    failed_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: Decimal
    average_latency_ms: float

    def __post_init__(self) -> None:
        ensure_not_blank(self.provider, "provider")
        ensure_not_blank(self.model_name, "model_name")

        if self.call_count < 0:
            raise ValueError("call_count must not be negative")

        if self.succeeded_count < 0:
            raise ValueError("succeeded_count must not be negative")

        if self.failed_count < 0:
            raise ValueError("failed_count must not be negative")

        if self.call_count != self.succeeded_count + self.failed_count:
            raise ValueError(
                "call_count must equal succeeded_count plus failed_count",
            )

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

        if self.average_latency_ms < 0:
            raise ValueError("average_latency_ms must not be negative")