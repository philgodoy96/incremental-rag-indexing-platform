import json
from collections.abc import Sequence
from decimal import Decimal
from time import perf_counter
from typing import Any, Protocol, cast

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from app.providers.llm import (
    LLMContextChunk,
    LLMGenerationRequest,
    LLMGenerationResponse,
    LLMProposedCitation,
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
        output_text = self._extract_output_text(response)

        if not output_text.strip():
            raise LLMProviderError("OpenAI response output_text was empty")

        answer, citations = self._parse_structured_output(output_text)
        prompt_tokens, completion_tokens = self._extract_usage(response)

        return LLMGenerationResponse(
            answer=answer,
            citations=citations,
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
            "Answer using only the provided retrieval context. "
            "If the context is insufficient, say that the provided context "
            "does not contain enough information. "
            "Do not invent facts. "
            "Return a single JSON object with keys "
            '"answer" (string) and "citations" (array). '
            "Each citation must include "
            '"candidate_id" (exact candidate_id string from the context) and '
            '"evidence_span" (non-empty verbatim substring copied from that '
            "candidate's content). "
            "Use only candidate_id values supplied in the context. "
            "Do not invent candidate references. "
            "Do not wrap the JSON in markdown fences."
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
            f"[candidate_id={chunk.candidate_id} rank={chunk.rank}] "
            f"{heading_context}\n"
            f"{chunk.content}"
        )

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)

        if isinstance(output_text, str):
            return output_text

        raise LLMProviderError("OpenAI response did not include output_text")

    def _parse_structured_output(
        self,
        output_text: str,
    ) -> tuple[str, tuple[LLMProposedCitation, ...]]:
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise LLMProviderError(
                "OpenAI response was not valid JSON for the generation contract",
            ) from error

        if not isinstance(payload, dict):
            raise LLMProviderError(
                "OpenAI response JSON must be an object with answer and citations",
            )

        answer = payload.get("answer")

        if not isinstance(answer, str) or not answer.strip():
            raise LLMProviderError(
                "OpenAI response JSON answer must be a non-empty string",
            )

        raw_citations = payload.get("citations")

        if not isinstance(raw_citations, list):
            raise LLMProviderError(
                "OpenAI response JSON citations must be an array",
            )

        citations: list[LLMProposedCitation] = []

        for raw_citation in raw_citations:
            if not isinstance(raw_citation, dict):
                raise LLMProviderError(
                    "OpenAI response JSON citations must contain objects",
                )

            candidate_id = raw_citation.get("candidate_id")
            evidence_span = raw_citation.get("evidence_span")

            if not isinstance(candidate_id, str) or not candidate_id.strip():
                raise LLMProviderError(
                    "OpenAI citation candidate_id must be a non-empty string",
                )

            if not isinstance(evidence_span, str):
                raise LLMProviderError(
                    "OpenAI citation evidence_span must be a string",
                )

            citations.append(
                LLMProposedCitation(
                    candidate_id=candidate_id,
                    evidence_span=evidence_span,
                ),
            )

        return answer, tuple(citations)

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
