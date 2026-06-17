# LLM Provider Observability

## Purpose

LLM provider observability records metadata about calls made to language model providers during answer generation.

Before integrating a real provider such as OpenAI or AWS Bedrock, the platform needs a durable way to inspect provider usage, latency, token counts, cost, and failures.

This slice introduces LLMProviderCallRecord and enriches the LLM provider boundary with usage metadata.

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

- expose LLM provider call read APIs
- calculate real provider costs
- persist failed provider calls from exception paths
- track prompt template versions
- track provider request/response IDs
- support fallback models
- support provider retries
- support per-tenant budgets
- support cost dashboards

## Future Work

Future slices should add:

- provider call read API
- failed provider call persistence
- real provider adapters
- token and cost calculation by provider/model
- prompt version metadata
- fallback model strategy
- retry and timeout handling
- budget alerts
- provider latency metrics
- dashboards for cost and reliability