# ADR-018: Expose LLM Provider Call Read API

## Status

Accepted

## Context

The platform persists LLMProviderCallRecord during grounded answer generation.

These records contain provider/model metadata, token usage, estimated cost, latency, status, timestamps, and links to answer_id and query_trace_id.

Without read endpoints, this data is only available through direct database inspection.

For a production-style RAG platform, provider call observability must be accessible through API boundaries so it can support debugging, admin tooling, evaluation workflows, and future dashboards.

## Decision

The system will expose LLM provider call read APIs:

- GET /api/v1/llm-provider-calls
- GET /api/v1/llm-provider-calls/{provider_call_id}
- GET /api/v1/answers/{answer_id}/llm-provider-calls

The top-level list endpoint supports filtering by:

- status
- provider
- model_name

The answer-scoped endpoint validates that the parent answer exists.

## Consequences

### Positive

- LLM provider calls become inspectable through the API.
- Engineers can debug cost, token usage, latency, and model selection.
- Provider activity can be tied back to answer_id and query_trace_id.
- The platform is better prepared for real provider integration.
- Future admin and evaluation tools can reuse these endpoints.

### Negative

- Adds additional API surface area.
- Provider call data may expose sensitive metadata.
- Offset pagination is not ideal for large datasets.
- Authorization and tenant scoping are still deferred.
- Cost aggregation is still not implemented.

## Alternatives Considered

### Keep Provider Calls Database-Only

Rejected because direct database inspection is not enough for product workflows, admin tooling, or portfolio-grade API design.

### Expose Provider Calls Only Through Answer Detail

Rejected because engineers also need top-level filtering across calls, providers, models, and statuses.

### Add Cost Dashboards Immediately

Deferred because dashboards should be built on top of stable read APIs and aggregation endpoints.

## Follow-Up

Future work should add:

- cursor pagination
- tenant/workspace scoping
- date range filters
- cost aggregation endpoints
- provider latency summaries
- failed call debugging views
- prompt version metadata
- provider request IDs
- authorization rules