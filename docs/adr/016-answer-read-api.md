# ADR-016: Expose Answer Read API

## Status

Accepted

## Context

The platform now persists grounded answers and answer citations.

The Grounded Answer API returns answer_id, but without read endpoints the persisted answer cannot be inspected through the API.

For a production-style RAG platform, answer inspection is required for debugging, auditability, evaluation, and future admin tooling.

## Decision

The system will expose read endpoints for persisted answers:

- GET /api/v1/answers
- GET /api/v1/answers/{answer_id}

The list endpoint supports basic filtering by status, provider, and model_name.

The detail endpoint returns the answer plus its persisted citations ordered by rank.

## Consequences

### Positive

- Persisted answers become inspectable through the API.
- API consumers can follow answer_id returned from answer generation.
- Citations can be inspected with the final answer.
- The system now supports a basic answer audit workflow.
- Prepares the platform for evaluation and admin tooling.

### Negative

- Adds more API surface area.
- Answer data may contain sensitive user questions, generated text, and citation quotes.
- Offset pagination is simple but may not scale well for very large datasets.
- Authorization and tenant scoping are still deferred.

## Alternatives Considered

### Do Not Expose Answer Read API

The system could persist answers only for database-level inspection.

Rejected because API-level inspection is useful for debugging, demos, automated tests, and future admin interfaces.

### Rely Only on Query Trace Read API

Query traces explain retrieval behavior, but they do not store the final answer returned to the user.

Rejected because retrieval auditability and answer auditability are different concerns.

### Implement Cursor Pagination Immediately

Cursor pagination is better for high-volume production datasets.

Deferred because offset pagination is sufficient for the first read API and keeps the slice small.

## Follow-Up

Future work should add:

- cursor pagination
- tenant/workspace access control
- date filtering
- sensitive content redaction
- answer evaluation results
- LLM token and cost metadata
- prompt version metadata