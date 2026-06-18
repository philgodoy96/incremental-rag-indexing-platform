from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from app.application.configuration.llm_provider_settings import (
    LLMProviderRuntimeSettings,
)
from app.providers.fake_llm_provider import FakeLLMProvider
from app.providers.llm_provider_factory import build_llm_provider
from app.providers.openai_llm_provider import OpenAILLMProvider, OpenAIResponsesClient


class FakeResponsesClient:
    def create(self, **kwargs: Any) -> Any:
        return SimpleNamespace(
            output_text="Test answer.",
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses: OpenAIResponsesClient = FakeResponsesClient()


def make_settings(
    *,
    provider: str = "fake",
    openai_api_key: str | None = None,
) -> LLMProviderRuntimeSettings:
    return LLMProviderRuntimeSettings(
        provider=provider,
        openai_api_key=openai_api_key,
        openai_model="gpt-5.4-mini",
        openai_timeout_seconds=30.0,
        openai_max_output_tokens=800,
        openai_input_price_per_1m_tokens_usd=Decimal("0.75"),
        openai_output_price_per_1m_tokens_usd=Decimal("4.50"),
    )


def test_build_llm_provider_returns_fake_provider_by_default() -> None:
    provider = build_llm_provider(make_settings(provider="fake"))

    assert isinstance(provider, FakeLLMProvider)


def test_build_llm_provider_returns_openai_provider_when_configured() -> None:
    provider = build_llm_provider(
        make_settings(
            provider="openai",
            openai_api_key="test-api-key",
        ),
        openai_client=FakeOpenAIClient(),
    )

    assert isinstance(provider, OpenAILLMProvider)
    assert provider.provider == "openai"


def test_build_llm_provider_requires_openai_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required when LLM_PROVIDER=openai",
    ):
        build_llm_provider(make_settings(provider="openai"))


def test_build_llm_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="llm provider must be one of"):
        build_llm_provider(make_settings(provider="unknown"))