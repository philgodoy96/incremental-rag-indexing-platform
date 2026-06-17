# ADR-017: Add LLM Provider Observability

## Status

Accepted

## Context

The platform supports grounded answer generation and answer persistence.

The next step before integrating a real LLM provider is to observe LLM calls.

Real provider calls introduce cost, latency, failures, token accounting, and vendor-specific behavior.

Without provider call observability, the system cannot answer operational questions about cost, performance, and reliability.

## Decision

The system will introduce LLM provider observability through:

- LLMUsageMetadata in the provider boundary
- LLMProviderCallRecord in the domain
- SQLAlchemy persistence for provider call records
- AnsweringTransaction support for provider call persistence
- GroundedAnswerService persistence of successful provider calls

LLMProviderCallRecord will link to:

- answer_id
- query_trace_id

## Consequences

### Positive

- Enables cost and token tracking.
- Connects LLM usage to persisted answers.
- Connects LLM usage to retrieval traces.
- Prepares the platform for real provider adapters.
- Supports future provider comparison and monitoring.
- Keeps fake provider tests deterministic and free.

### Negative

- Adds additional persistence writes during answer generation.
- Adds more domain and infrastructure complexity.
- Current implementation only persists successful provider calls.
- Cost calculation is still fake and must be implemented per real provider.
- Provider read APIs are still needed.

## Alternatives Considered

### Integrate OpenAI or Bedrock First

The platform could integrate a real provider before adding observability.

Rejected because real provider usage should be measurable from the beginning.

### Track Cost Only in Logs

Structured logs are useful, but they are not sufficient for answer-level auditability, cost analysis, or admin tooling.

Rejected because provider calls are domain data in this platform.

### Store Provider Usage Inside AnswerRecord

The system could store token usage directly on AnswerRecord.

Rejected because an answer may eventually involve multiple provider calls, retries, fallback models, evaluators, or post-processing calls.

A separate LLMProviderCallRecord is more extensible.

## Follow-Up

Future work should add:

- provider call read APIs
- failed call persistence
- real provider cost calculation
- prompt version tracking
- provider request IDs
- fallback model tracking
- retry metadata
- tenant/workspace cost attribution
- cost dashboards