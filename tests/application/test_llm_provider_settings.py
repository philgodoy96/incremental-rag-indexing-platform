from decimal import Decimal

import pytest

from app.application.configuration.llm_provider_settings import (
    LLMProviderRuntimeSettings,
)


def make_settings(
    *,
    provider: str = "fake",
    openai_api_key: str | None = None,
    openai_model: str = "gpt-5.4-mini",
    openai_timeout_seconds: float = 30.0,
    openai_max_output_tokens: int = 800,
    openai_input_price_per_1m_tokens_usd: Decimal = Decimal("0.75"),
    openai_output_price_per_1m_tokens_usd: Decimal = Decimal("4.50"),
) -> LLMProviderRuntimeSettings:
    return LLMProviderRuntimeSettings(
        provider=provider,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_timeout_seconds=openai_timeout_seconds,
        openai_max_output_tokens=openai_max_output_tokens,
        openai_input_price_per_1m_tokens_usd=openai_input_price_per_1m_tokens_usd,
        openai_output_price_per_1m_tokens_usd=openai_output_price_per_1m_tokens_usd,
    )


def test_fake_provider_does_not_require_openai_api_key() -> None:
    settings = make_settings(provider="fake", openai_api_key=None)

    settings.validate()


def test_openai_provider_requires_api_key() -> None:
    settings = make_settings(provider="openai", openai_api_key=None)

    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required when LLM_PROVIDER=openai",
    ):
        settings.validate()


def test_openai_provider_accepts_api_key() -> None:
    settings = make_settings(
        provider="openai",
        openai_api_key="test-api-key",
    )

    settings.validate()


def test_rejects_unknown_provider() -> None:
    settings = make_settings(provider="unknown")

    with pytest.raises(ValueError, match="llm provider must be one of"):
        settings.validate()


def test_rejects_blank_openai_model() -> None:
    settings = make_settings(openai_model=" ")

    with pytest.raises(ValueError, match="OPENAI_MODEL must not be blank"):
        settings.validate()


def test_rejects_non_positive_timeout() -> None:
    settings = make_settings(openai_timeout_seconds=0)

    with pytest.raises(
        ValueError,
        match="OPENAI_TIMEOUT_SECONDS must be greater than zero",
    ):
        settings.validate()


def test_rejects_non_positive_max_output_tokens() -> None:
    settings = make_settings(openai_max_output_tokens=0)

    with pytest.raises(
        ValueError,
        match="OPENAI_MAX_OUTPUT_TOKENS must be greater than zero",
    ):
        settings.validate()


def test_rejects_negative_input_price() -> None:
    settings = make_settings(
        openai_input_price_per_1m_tokens_usd=Decimal("-1"),
    )

    with pytest.raises(
        ValueError,
        match="OPENAI_INPUT_PRICE_PER_1M_TOKENS_USD must not be negative",
    ):
        settings.validate()


def test_rejects_negative_output_price() -> None:
    settings = make_settings(
        openai_output_price_per_1m_tokens_usd=Decimal("-1"),
    )

    with pytest.raises(
        ValueError,
        match="OPENAI_OUTPUT_PRICE_PER_1M_TOKENS_USD must not be negative",
    ):
        settings.validate()