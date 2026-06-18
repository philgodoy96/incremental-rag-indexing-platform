from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from openai import APITimeoutError

from app.providers.llm import (
    LLMContextChunk,
    LLMGenerationRequest,
    LLMProviderError,
)
from app.providers.openai_llm_provider import OpenAILLMProvider, OpenAIResponsesClient


class FakeResponsesClient:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return self.response


class FakeOpenAIClient:
    def __init__(self, responses: OpenAIResponsesClient) -> None:
        self.responses = responses


def make_provider(
    *,
    responses: FakeResponsesClient,
    model_name: str = "gpt-5.4-mini",
) -> OpenAILLMProvider:
    return OpenAILLMProvider(
        api_key="test-api-key",
        model_name=model_name,
        timeout_seconds=30.0,
        max_output_tokens=800,
        input_price_per_1m_tokens_usd=Decimal("0.75"),
        output_price_per_1m_tokens_usd=Decimal("4.50"),
        client=FakeOpenAIClient(responses),
    )


def make_request() -> LLMGenerationRequest:
    return LLMGenerationRequest(
        question="Who owns Project Atlas?",
        context_chunks=(
            LLMContextChunk(
                rank=1,
                content=(
                    "Project Atlas is owned by the Platform Intelligence team. "
                    "The accountable engineering manager is Maya Chen."
                ),
                heading_context=("Project Atlas Brief", "Ownership"),
            ),
        ),
    )


def test_openai_llm_provider_generates_answer_from_responses_api() -> None:
    fake_response = SimpleNamespace(
        output_text=(
            "Project Atlas is owned by the Platform Intelligence team. "
            "Maya Chen is the accountable engineering manager."
        ),
        usage=SimpleNamespace(
            input_tokens=100,
            output_tokens=40,
            total_tokens=140,
        ),
    )
    responses = FakeResponsesClient(response=fake_response)
    provider = make_provider(responses=responses)

    response = provider.generate_answer(make_request())

    assert response.answer == (
        "Project Atlas is owned by the Platform Intelligence team. "
        "Maya Chen is the accountable engineering manager."
    )
    assert response.usage.provider == "openai"
    assert response.usage.model_name == "gpt-5.4-mini"
    assert response.usage.prompt_tokens == 100
    assert response.usage.completion_tokens == 40
    assert response.usage.total_tokens == 140
    assert response.usage.estimated_cost_usd == Decimal("0.000255")
    assert response.usage.latency_ms >= 0

    assert len(responses.calls) == 1

    call = responses.calls[0]

    assert call["model"] == "gpt-5.4-mini"
    assert call["max_output_tokens"] == 800
    assert "grounded enterprise knowledge assistant" in call["instructions"]
    assert "Who owns Project Atlas?" in call["input"]
    assert "Project Atlas Brief > Ownership" in call["input"]


def test_openai_llm_provider_returns_zero_usage_when_usage_is_missing() -> None:
    fake_response = SimpleNamespace(
        output_text="The context does not contain enough information.",
        usage=None,
    )
    responses = FakeResponsesClient(response=fake_response)
    provider = make_provider(responses=responses)

    response = provider.generate_answer(make_request())

    assert response.usage.prompt_tokens == 0
    assert response.usage.completion_tokens == 0
    assert response.usage.total_tokens == 0
    assert response.usage.estimated_cost_usd == Decimal("0.000")


def test_openai_llm_provider_supports_legacy_usage_attribute_names() -> None:
    fake_response = SimpleNamespace(
        output_text="Project Atlas is owned by Platform Intelligence.",
        usage=SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
    )
    responses = FakeResponsesClient(response=fake_response)
    provider = make_provider(responses=responses)

    response = provider.generate_answer(make_request())

    assert response.usage.prompt_tokens == 10
    assert response.usage.completion_tokens == 5
    assert response.usage.total_tokens == 15


def test_openai_llm_provider_maps_timeout_error() -> None:
    responses = FakeResponsesClient(
        error=APITimeoutError(
            request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
        ),
    )
    provider = make_provider(responses=responses)

    with pytest.raises(LLMProviderError, match="OpenAI request timed out"):
        provider.generate_answer(make_request())


def test_openai_llm_provider_rejects_empty_output_text() -> None:
    fake_response = SimpleNamespace(
        output_text=" ",
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=0,
            total_tokens=10,
        ),
    )
    responses = FakeResponsesClient(response=fake_response)
    provider = make_provider(responses=responses)

    with pytest.raises(
        LLMProviderError,
        match="OpenAI response output_text was empty",
    ):
        provider.generate_answer(make_request())


def test_openai_llm_provider_rejects_response_without_output_text() -> None:
    fake_response = SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        ),
    )
    responses = FakeResponsesClient(response=fake_response)
    provider = make_provider(responses=responses)

    with pytest.raises(
        LLMProviderError,
        match="OpenAI response did not include output_text",
    ):
        provider.generate_answer(make_request())


def test_openai_llm_provider_rejects_blank_api_key() -> None:
    with pytest.raises(ValueError, match="api_key must not be blank"):
        OpenAILLMProvider(
            api_key=" ",
            model_name="gpt-5.4-mini",
            timeout_seconds=30.0,
            max_output_tokens=800,
            input_price_per_1m_tokens_usd=Decimal("0.75"),
            output_price_per_1m_tokens_usd=Decimal("4.50"),
        )


def test_openai_llm_provider_rejects_invalid_max_output_tokens() -> None:
    with pytest.raises(
        ValueError,
        match="max_output_tokens must be greater than zero",
    ):
        OpenAILLMProvider(
            api_key="test-api-key",
            model_name="gpt-5.4-mini",
            timeout_seconds=30.0,
            max_output_tokens=0,
            input_price_per_1m_tokens_usd=Decimal("0.75"),
            output_price_per_1m_tokens_usd=Decimal("4.50"),
        )