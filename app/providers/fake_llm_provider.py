from decimal import Decimal
from time import perf_counter

from app.providers.llm import (
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMProvider,
    LLMUsageMetadata,
)


class FakeLLMProvider(LLMProvider):
    def __init__(
        self,
        *,
        provider: str = "fake",
        model_name: str = "fake-llm-v1",
    ) -> None:
        self._provider = provider
        self._model_name = model_name

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_answer(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        started_at = perf_counter()

        first_chunk = request.context_chunks[0]
        answer = f"Based on the retrieved context, {first_chunk.content}"

        prompt_tokens = self._estimate_tokens(
            request.question,
            *[chunk.content for chunk in request.context_chunks],
        )
        completion_tokens = self._estimate_tokens(answer)

        latency_ms = int((perf_counter() - started_at) * 1000)

        return LLMGenerationResponse(
            answer=answer,
            usage=LLMUsageMetadata(
                provider=self._provider,
                model_name=self._model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=Decimal("0"),
                latency_ms=latency_ms,
            ),
        )

    def _estimate_tokens(self, *texts: str) -> int:
        joined_text = " ".join(texts)
        word_count = len(joined_text.split())

        return max(word_count, 1)