# LLM Provider Observability

## Purpose

LLM provider observability records metadata about calls made to language model providers during answer generation.

The platform persists provider usage, latency, token counts, estimated cost, and failures so teams can inspect LLM behavior without relying on external dashboards alone.

This document describes LLMProviderCallRecord and the LLM provider boundary usage metadata model.

## Why This Matters

LLM calls cost money and can fail.

A production RAG platform needs to answer questions such as:

- Which provider was called?
- Which model was used?
- How many prompt tokens were consumed?
- How many completion tokens were consumed?
- What was the estimated cost?
- How long did the provider call take?
- Did the call succeed or fail?
- Which answer_id did this call produce?
- Which query_trace_id was associated with the answer?

Without this data, teams cannot reliably debug latency, monitor cost, compare providers, or detect regressions.

## Data Model

The main persisted record is:

- LLMProviderCallRecord

## LLMProviderCallRecord

LLMProviderCallRecord stores metadata about one LLM provider call.

It includes:

- id
- answer_id
- query_trace_id
- provider
- model_name
- status
- prompt_tokens
- completion_tokens
- total_tokens
- estimated_cost_usd
- latency_ms
- started_at
- completed_at
- error_message
- created_at

## Status

Supported statuses:

- succeeded
- failed

A succeeded provider call has token usage, estimated cost, latency, and no error_message.

A failed provider call must include error_message.

## Provider Boundary

The LLMProvider interface returns LLMGenerationResponse.

LLMGenerationResponse includes:

- answer
- usage

The usage object includes:

- provider
- model_name
- prompt_tokens
- completion_tokens
- total_tokens
- estimated_cost_usd
- latency_ms

This keeps provider metadata close to the provider adapter while keeping answer persistence in the application service.

## FakeLLMProvider

FakeLLMProvider returns deterministic answers and fake usage metadata.

It estimates tokens using a simple word-count approximation and returns zero estimated cost.

This is intentional.

The fake provider exists to validate architecture, tests, and persistence without making real paid API calls.

## Answer Generation Integration

During answer generation:

1. GroundedAnswerService retrieves context.
2. If no chunks are retrieved, it returns insufficient_context and does not call the LLM.
3. If chunks exist, it calls LLMProvider.
4. The provider returns answer text and usage metadata.
5. GroundedAnswerService persists AnswerRecord and AnswerCitationRecord.
6. GroundedAnswerService persists LLMProviderCallRecord linked to answer_id and query_trace_id.

## Why insufficient_context Does Not Create Provider Calls

When retrieval returns no chunks, the system does not call the LLM.

Therefore, no LLMProviderCallRecord is created.

This avoids recording fake LLM activity for requests that were safely refused before generation.

## Audit Chain

The full audit chain becomes:

    AnswerRecord
    -> LLMProviderCallRecord
    -> query_trace_id
    -> QueryTrace
    -> QueryTraceHit
    -> ChunkVersion
    -> DocumentVersion

This supports debugging across answer generation, provider usage, retrieval behavior, and source data.

## Current Limitations

The current implementation does not yet:

- track prompt template versions
- track provider request/response IDs
- support fallback models
- support provider retries or automatic fallback
- support per-tenant budgets
- expose bundled cost or reliability dashboards

OpenAI is supported as an optional LLM provider. Estimated cost for OpenAI calls depends on configured pricing and returned usage metadata. Fake provider calls use deterministic test metadata and zero estimated cost.

Failed provider calls are persisted when answer generation fails after retrieval succeeds. Provider call read APIs and usage reporting APIs are available for inspection.

## Future Work

Future hardening may add:

- additional real provider adapters
- prompt version metadata
- fallback model strategy
- retry and timeout policy
- budget alerts
- deployment-time dashboards for cost and reliability