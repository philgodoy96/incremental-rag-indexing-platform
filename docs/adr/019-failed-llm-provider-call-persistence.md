# ADR-019: Persist Failed LLM Provider Calls

## Status

Accepted

## Context

The platform records successful LLM provider calls during grounded answer generation.

However, failed provider calls were not persisted.

In production, provider failures are operationally important. They affect reliability, cost monitoring, incident response, user experience, and provider selection.

A provider failure should leave an audit trail even when no answer is produced.

## Decision

The system will persist failed LLM provider calls when the LLM provider fails after retrieval succeeds.

The persisted failed call will include:

- answer_id = null
- query_trace_id
- provider
- model_name
- status = failed
- zero token usage for now
- zero estimated cost for now
- latency_ms
- error_message

The LLMProvider interface will expose provider and model_name so the application can persist provider identity even when generate_answer raises an exception.

Known provider failures use LLMProviderError.

Unexpected exceptions are persisted and then wrapped as LLMProviderError.

## Consequences

### Positive

- Provider failures become auditable.
- Failed calls are visible through existing provider call read APIs.
- Debugging improves because failures are linked to query_trace_id.
- The system can distinguish retrieval insufficiency from provider failure.
- The platform is better prepared for real LLM providers.
- Future reliability dashboards can use persisted failure data.

### Negative

- The answer generation service now has additional error-handling complexity.
- Failed calls currently store zero token/cost usage even though some providers may expose partial usage.
- Failed calls currently do not create failed AnswerRecord records.
- Provider error taxonomy is still unstructured.
- Retry and fallback metadata are still missing.

## Alternatives Considered

### Log Provider Failures Only

Rejected because logs are useful but insufficient for answer-level auditability, read APIs, reporting, and long-term analysis.

### Create Failed AnswerRecord for Provider Failures

Deferred.

A provider failure is different from an insufficient-context answer. The platform may later introduce failed answer records, but the immediate need is provider-call auditability.

### Persist Failures Only After Retries

Rejected for now.

Every provider attempt should be observable. Retry metadata can be added later.

## Follow-Up

Future work should add:

- provider error categories
- retry attempt tracking
- fallback model tracking
- provider request IDs
- partial token usage on failed calls
- failed answer records
- request_id and trace_id correlation
- provider reliability aggregation APIs