# ADR-003: Separate Health Checks from Readiness Checks

## Status

Accepted

## Context

The application needs operational endpoints that help determine whether it is alive and whether it is ready to serve traffic.

A common mistake is to make one health endpoint check every dependency.

That can cause incorrect behavior in production.

For example, if the database is temporarily unavailable, the API process may still be healthy. Restarting the API process does not necessarily fix the database dependency.

## Decision

The system will expose separate endpoints:

    GET /api/v1/health
    GET /api/v1/readiness

Health checks whether the API process is alive.

Readiness checks whether required dependencies are available.

In this slice, readiness checks:

- Postgres connectivity
- pgvector extension availability

## Alternatives Considered

### Single Health Endpoint for Everything

This is simpler, but it mixes process health with dependency readiness.

Rejected because it can lead to misleading operational behavior.

### No Readiness Endpoint Until Production

This would reduce initial implementation work.

Rejected because readiness is a foundational operational concept and helps validate database setup early.

## Consequences

### Positive

- Clearer operational semantics
- Better production readiness
- Easier debugging
- Better Kubernetes/container compatibility later
- Clear distinction between process availability and dependency availability

### Negative

- Slightly more code
- More testing cases
- Developers must understand which endpoint to use in each situation

## Follow-Up

Future readiness checks may include:

- migration version compatibility
- embedding provider availability
- queue availability
- object storage availability
- vector index status