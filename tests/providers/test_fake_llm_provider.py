from decimal import Decimal

import pytest

from app.providers.fake_llm_provider import FakeLLMProvider
from app.providers.llm import (
    LLMContextChunk,
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMProviderError,
    LLMUsageMetadata,
)


def test_llm_provider_error_rejects_blank_message() -> None:
    with pytest.raises(ValueError, match="message must not be blank"):
        LLMProviderError(" ")


def test_llm_context_chunk_rejects_invalid_rank() -> None:
    with pytest.raises(ValueError, match="rank must be greater"):
        LLMContextChunk(
            rank=0,
            content="Status: At Risk",
            heading_context=("Project Atlas Status", "Summary"),
        )


def test_llm_generation_request_requires_context_chunks() -> None:
    with pytest.raises(ValueError, match="context_chunks must not be empty"):
        LLMGenerationRequest(
            question="What is Project Atlas status?",
            context_chunks=(),
        )


def test_llm_usage_metadata_rejects_invalid_total_tokens() -> None:
    with pytest.raises(
        ValueError,
        match="total_tokens must equal prompt_tokens plus completion_tokens",
    ):
        LLMUsageMetadata(
            provider="fake",
            model_name="fake-llm-v1",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=99,
            estimated_cost_usd=Decimal("0"),
            latency_ms=1,
        )


def test_llm_usage_metadata_rejects_negative_cost() -> None:
    with pytest.raises(ValueError, match="estimated_cost_usd must not be negative"):
        LLMUsageMetadata(
            provider="fake",
            model_name="fake-llm-v1",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=Decimal("-0.01"),
            latency_ms=1,
        )


def test_llm_generation_response_rejects_blank_answer() -> None:
    with pytest.raises(ValueError, match="answer must not be blank"):
        LLMGenerationResponse(
            answer=" ",
            usage=LLMUsageMetadata(
                provider="fake",
                model_name="fake-llm-v1",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                estimated_cost_usd=Decimal("0"),
                latency_ms=1,
            ),
        )


def test_fake_llm_provider_exposes_provider_identity() -> None:
    provider = FakeLLMProvider(provider="fake-provider", model_name="fake-model")

    assert provider.provider == "fake-provider"
    assert provider.model_name == "fake-model"


def test_fake_llm_provider_generates_deterministic_answer_from_first_chunk() -> None:
    provider = FakeLLMProvider()

    response = provider.generate_answer(
        LLMGenerationRequest(
            question="What is Project Atlas status?",
            context_chunks=(
                LLMContextChunk(
                    rank=1,
                    content="Status: At Risk",
                    heading_context=("Project Atlas Status", "Summary"),
                ),
                LLMContextChunk(
                    rank=2,
                    content="Owner: Platform Team",
                    heading_context=("Project Atlas Status", "Ownership"),
                ),
            ),
        ),
    )

    assert response.answer == "Based on the retrieved context, Status: At Risk"


def test_fake_llm_provider_returns_usage_metadata() -> None:
    provider = FakeLLMProvider()

    response = provider.generate_answer(
        LLMGenerationRequest(
            question="What is Project Atlas status?",
            context_chunks=(
                LLMContextChunk(
                    rank=1,
                    content="Status: At Risk",
                    heading_context=("Project Atlas Status", "Summary"),
                ),
            ),
        ),
    )

    assert response.usage.provider == "fake"
    assert response.usage.model_name == "fake-llm-v1"
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.usage.total_tokens == (
        response.usage.prompt_tokens + response.usage.completion_tokens
    )
    assert response.usage.estimated_cost_usd == Decimal("0")
    assert response.usage.latency_ms >= 0