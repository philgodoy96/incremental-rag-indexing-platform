import pytest

from app.providers.fake_llm_provider import FakeLLMProvider
from app.providers.llm import (
    LLMContextChunk,
    LLMGenerationRequest,
    LLMGenerationResponse,
)


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


def test_llm_generation_response_rejects_blank_answer() -> None:
    with pytest.raises(ValueError, match="answer must not be blank"):
        LLMGenerationResponse(answer=" ")


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