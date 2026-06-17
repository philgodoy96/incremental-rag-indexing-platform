# ADR-020: Add LLM Usage Reporting API

## Status

Accepted

## Context

The platform persists LLMProviderCallRecord entries for both successful and failed provider calls.

Individual provider call records are useful for auditability, but production systems also need aggregate reporting.

Engineering and product teams need visibility into usage, cost, latency, and reliability by period, provider, and model.

Without aggregate reporting, cost and reliability analysis requires manual database queries.

## Decision

The system will introduce an LLM Usage Reporting API with:

- GET /api/v1/llm-usage/summary
- GET /api/v1/llm-usage/by-model

The reporting layer will be modeled separately from individual provider call read APIs.

A new LLMUsageReportRepository will aggregate data from LLMProviderCallRecord records.

The API will support filters for:

- started_at_from
- started_at_to
- provider
- model_name

The API will serialize estimated_cost_usd as a string to preserve Decimal semantics.

## Consequences

### Positive

- LLM usage becomes visible at an operational level.
- Cost reporting is now available through API boundaries.
- Provider/model comparison becomes possible.
- Failure counts and average latency can be inspected.
- The platform better satisfies the cost observability goal.
- Future dashboards can build on stable reporting APIs.

### Negative

- Adds aggregation queries that may become expensive at scale.
- Offset/cursor concerns are replaced by aggregation performance concerns.
- There is no caching or materialized view yet.
- No tenant/workspace attribution exists yet.
- Reporting is still basic and not time-series oriented.

## Alternatives Considered

### Use Only Provider Call Read API

Rejected because individual records are not enough for operational reporting.

### Add Dashboards Directly

Deferred because dashboards should be built on top of stable APIs and aggregation contracts.

### Store Precomputed Aggregates Immediately

Deferred because raw provider call volume is still small in the current project stage.

At larger scale, materialized views or scheduled aggregation tables may be introduced.

## Follow-Up

Future work should add:

- daily aggregation
- tenant/workspace attribution
- budget alerts
- p95/p99 latency
- failure rate percentage
- provider error category breakdown
- dashboard endpoints
- materialized views or precomputed reporting tables