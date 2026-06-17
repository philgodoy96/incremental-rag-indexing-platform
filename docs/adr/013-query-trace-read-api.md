# ADR-013: Expose Query Trace Read API

## Status

Accepted

## Context

The platform persists QueryTrace and QueryTraceHit records during semantic retrieval.

The retrieval API returns query_trace_id, but without read endpoints the trace cannot be inspected through the API.

For a production-style RAG platform, retrieval observability should be available as product/domain data, not only as logs.

## Decision

The system will expose read endpoints for query traces:

- GET /api/v1/retrieval/traces
- GET /api/v1/retrieval/traces/{trace_id}

The list endpoint supports basic filtering by status, provider, and model_name.

The detail endpoint returns the trace plus its retrieved hits ordered by rank.

## Consequences

### Positive

- Makes retrieval executions inspectable.
- Supports debugging bad semantic search results.
- Prepares the platform for grounded answer auditability.
- Allows API consumers to follow query_trace_id returned by semantic search.
- Keeps retrieval observability separate from logs.

### Negative

- Adds additional API surface area.
- Query trace data may contain sensitive query text and retrieved content.
- Offset pagination may not scale well for very large datasets.
- Requires future authorization and retention policies.

## Alternatives Considered

### Do Not Expose Trace Read API

The system could persist traces only for internal database inspection.

Rejected because API-level inspection is useful for debugging, demos, and future admin tooling.

### Rely Only on Logs

Structured logs are useful for operations, but they are not ideal for product-level trace inspection.

Rejected because query traces are domain data and should be queryable.

### Implement Cursor Pagination Immediately

Cursor pagination is better for large datasets, but offset pagination is simpler for this first API.

Deferred until trace volume or performance requirements justify it.

## Follow-Up

Future work should add:

- cursor pagination
- tenant/workspace access control
- date range filtering
- sensitive content redaction
- trace retention policies
- answer traces linked to query_trace_id