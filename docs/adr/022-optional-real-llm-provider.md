# ADR-022: Optional Real LLM Provider Integration

## Status

Accepted

## Context

The platform originally used fake providers for deterministic local development and testing.

Fake providers are valuable because they keep the project reproducible, cost-free, and safe for continuous integration.

However, a production-style AI platform should also demonstrate that the provider boundary can integrate with a real external LLM provider.

The project already persists grounded answers, citations, provider calls, usage metadata, and usage reports.

This makes it a good point to introduce an optional real provider adapter.

## Decision

The system will support an optional OpenAI LLM provider.

The fake provider remains the default.

OpenAI is enabled only through explicit runtime configuration.

The relevant environment variables are documented in `.env.example`.

Automated tests must not call OpenAI.

Provider selection is handled through a provider factory.

The Answer API contract does not change.

Provider call persistence, answer persistence, citations, and usage reporting should continue to work through the same application flow.

## Consequences

### Positive

- The project can demonstrate real external provider integration.
- The fake provider remains safe and deterministic.
- Tests stay cost-free and reliable.
- Provider implementation is isolated behind the existing LLM provider boundary.
- Usage and cost reporting can observe real provider calls.
- The architecture better resembles production AI systems.

### Negative

- Configuration becomes more complex.
- Real provider calls introduce cost.
- Real provider behavior introduces latency and variability.
- Provider SDK behavior may change over time.
- Model availability and pricing may change over time.
- Manual smoke tests are required to validate real behavior.

## Alternatives Considered

### Replace Fake Provider With OpenAI

Rejected.

This would make local development, tests, and GitHub usage dependent on external credentials and paid API calls.

### Keep Only Fake Provider

Rejected.

This would make the project less convincing as a production-style AI integration.

### Add OpenAI As Mandatory Dependency For All Environments

Rejected.

The real provider should be optional and explicitly enabled.

## Safety Rules

- Fake provider is the default.
- `.env` must never be committed.
- API keys must not appear in docs, logs, issues, pull requests, or tests.
- Automated tests must not call OpenAI.
- Real provider use is limited to controlled local demos.
- Model and pricing configuration must remain explicit and configurable.

## Follow-Up

Future work should add:

- budget guardrails
- request rate limits
- fallback model support
- retry strategy
- circuit breaker behavior
- provider-specific failure categories
- cost alerting
- documented comparison observations