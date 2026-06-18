from collections.abc import Sequence
from decimal import Decimal
from time import perf_counter
from typing import Any, Protocol, cast

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from app.providers.llm import (
    LLMContextChunk,
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMProvider,
    LLMProviderError,
    LLMUsageMetadata,
)


class OpenAIResponsesClient(Protocol):
    def create(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class OpenAIClientLike(Protocol):
    responses: OpenAIResponsesClient


class OpenAILLMProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: float,
        max_output_tokens: int,
        input_price_per_1m_tokens_usd: Decimal,
        output_price_per_1m_tokens_usd: Decimal,
        client: OpenAIClientLike | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key must not be blank")

        if not model_name or not model_name.strip():
            raise ValueError("model_name must not be blank")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        if max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be greater than zero")

        if input_price_per_1m_tokens_usd < Decimal("0"):
            raise ValueError("input_price_per_1m_tokens_usd must not be negative")

        if output_price_per_1m_tokens_usd < Decimal("0"):
            raise ValueError("output_price_per_1m_tokens_usd must not be negative")

        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max_output_tokens
        self._input_price_per_1m_tokens_usd = input_price_per_1m_tokens_usd
        self._output_price_per_1m_tokens_usd = output_price_per_1m_tokens_usd
        self._client: OpenAIClientLike = (
            client
            if client is not None
            else cast(
                OpenAIClientLike,
                OpenAI(
                    api_key=api_key,
                    timeout=timeout_seconds,
                ),
            )
        )

    @property
    def provider(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_answer(
        self,
        request: LLMGenerationRequest,
    ) -> LLMGenerationResponse:
        started_at = perf_counter()

        try:
            response = self._client.responses.create(
                model=self._model_name,
                instructions=self._build_instructions(),
                input=self._build_input(request),
                max_output_tokens=self._max_output_tokens,
            )
        except RateLimitError as error:
            raise LLMProviderError("OpenAI rate limit exceeded") from error
        except APITimeoutError as error:
            raise LLMProviderError("OpenAI request timed out") from error
        except APIConnectionError as error:
            raise LLMProviderError("OpenAI connection error") from error
        except APIError as error:
            raise LLMProviderError(f"OpenAI API error: {error}") from error
        except Exception as error:
            raise LLMProviderError(
                f"unexpected OpenAI provider error: {type(error).__name__}: {error}",
            ) from error

        latency_ms = int((perf_counter() - started_at) * 1000)
        answer = self._extract_output_text(response)

        if not answer.strip():
            raise LLMProviderError("OpenAI response output_text was empty")

        prompt_tokens, completion_tokens = self._extract_usage(response)

        return LLMGenerationResponse(
            answer=answer,
            usage=LLMUsageMetadata(
                provider=self.provider,
                model_name=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=self._estimate_cost_usd(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                ),
                latency_ms=latency_ms,
            ),
        )

    def _build_instructions(self) -> str:
        return (
            "You are a grounded enterprise knowledge assistant. "
            "Answer using only the provided context. "
            "If the context is insufficient, say that the provided context "
            "does not contain enough information. "
            "Do not invent facts."
        )

    def _build_input(self, request: LLMGenerationRequest) -> str:
        rendered_context = "\n\n".join(
            self._render_context_chunk(chunk)
            for chunk in request.context_chunks
        )

        return (
            "Question:\n"
            f"{request.question}\n\n"
            "Context:\n"
            f"{rendered_context}"
        )

    def _render_context_chunk(self, chunk: LLMContextChunk) -> str:
        heading_context = " > ".join(chunk.heading_context)

        return (
            f"[{chunk.rank}] {heading_context}\n"
            f"{chunk.content}"
        )

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)

        if isinstance(output_text, str):
            return output_text

        raise LLMProviderError("OpenAI response did not include output_text")

    def _extract_usage(self, response: Any) -> tuple[int, int]:
        usage = getattr(response, "usage", None)

        if usage is None:
            return (0, 0)

        prompt_tokens = self._extract_int_attr(
            usage,
            ("input_tokens", "prompt_tokens"),
        )
        completion_tokens = self._extract_int_attr(
            usage,
            ("output_tokens", "completion_tokens"),
        )

        return (prompt_tokens, completion_tokens)

    def _extract_int_attr(self, value: Any, names: Sequence[str]) -> int:
        for name in names:
            raw_value = getattr(value, name, None)

            if isinstance(raw_value, int):
                return raw_value

        return 0

    def _estimate_cost_usd(
        self,
        *,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> Decimal:
        input_cost = (
            Decimal(prompt_tokens)
            / Decimal("1000000")
            * self._input_price_per_1m_tokens_usd
        )
        output_cost = (
            Decimal(completion_tokens)
            / Decimal("1000000")
            * self._output_price_per_1m_tokens_usd
        )

        return input_cost + output_cost