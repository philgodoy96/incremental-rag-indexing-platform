from dataclasses import dataclass
from decimal import Decimal

SUPPORTED_LLM_PROVIDERS = {"fake", "openai"}


@dataclass(frozen=True, slots=True)
class LLMProviderRuntimeSettings:
    provider: str
    openai_api_key: str | None
    openai_model: str
    openai_timeout_seconds: float
    openai_max_output_tokens: int
    openai_input_price_per_1m_tokens_usd: Decimal
    openai_output_price_per_1m_tokens_usd: Decimal

    def validate(self) -> None:
        provider = self.provider.strip().lower()

        if provider not in SUPPORTED_LLM_PROVIDERS:
            raise ValueError(
                "llm provider must be one of: "
                f"{', '.join(sorted(SUPPORTED_LLM_PROVIDERS))}",
            )

        if provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai",
            )

        if not self.openai_model.strip():
            raise ValueError("OPENAI_MODEL must not be blank")

        if self.openai_timeout_seconds <= 0:
            raise ValueError("OPENAI_TIMEOUT_SECONDS must be greater than zero")

        if self.openai_max_output_tokens <= 0:
            raise ValueError("OPENAI_MAX_OUTPUT_TOKENS must be greater than zero")

        if self.openai_input_price_per_1m_tokens_usd < 0:
            raise ValueError(
                "OPENAI_INPUT_PRICE_PER_1M_TOKENS_USD must not be negative",
            )

        if self.openai_output_price_per_1m_tokens_usd < 0:
            raise ValueError(
                "OPENAI_OUTPUT_PRICE_PER_1M_TOKENS_USD must not be negative",
            )