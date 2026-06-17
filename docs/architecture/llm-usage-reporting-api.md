# LLM Usage Reporting API

## Purpose

The LLM Usage Reporting API exposes aggregated usage, cost, latency, and reliability metrics for LLM provider calls.

The platform already stores individual LLMProviderCallRecord entries.

Those records are useful for auditability, but product and engineering teams also need aggregated views to understand operational behavior over time.

This API turns raw provider call records into reporting data.

## Endpoints

### Usage Summary

GET /api/v1/llm-usage/summary

Supported query parameters:

- started_at_from
- started_at_to
- provider
- model_name

Example request:

    GET /api/v1/llm-usage/summary?provider=fake&model_name=fake-llm-v1

Example response:

    {
      "call_count": 3,
      "succeeded_count": 2,
      "failed_count": 1,
      "prompt_tokens": 100,
      "completion_tokens": 40,
      "total_tokens": 140,
      "estimated_cost_usd": "0.0123",
      "average_latency_ms": 125.5
    }

### Usage By Model

GET /api/v1/llm-usage/by-model

Supported query parameters:

- started_at_from
- started_at_to
- provider
- model_name

Example response:

    {
      "items": [
        {
          "provider": "fake",
          "model_name": "fake-llm-v1",
          "call_count": 3,
          "succeeded_count": 2,
          "failed_count": 1,
          "prompt_tokens": 100,
          "completion_tokens": 40,
          "total_tokens": 140,
          "estimated_cost_usd": "0.0123",
          "average_latency_ms": 125.5
        }
      ]
    }

## Why This API Matters

A production RAG platform needs more than individual request inspection.

Teams need to understand:

- total LLM usage
- cost trends
- provider/model cost comparison
- token consumption
- failure rates
- average latency
- operational regressions after prompt or model changes

This API creates the first operational reporting layer for LLM usage.

## Difference From Provider Call Read API

The LLM Provider Call Read API exposes individual records.

The LLM Usage Reporting API exposes aggregated summaries.

Provider call read APIs answer:

- What happened in this specific provider call?
- What was the error message?
- Which answer/query trace was linked?

Usage reporting APIs answer:

- How much did we spend?
- How many calls failed?
- Which provider/model is most used?
- What is average latency?

Both are needed.

## Domain Model

The reporting domain introduces:

- LLMUsageSummary
- LLMUsageByModelSummary
- LLMUsageReportRepository

These domain objects validate aggregate invariants before data reaches the API layer.

## Invariants

The reporting domain enforces:

- call_count must not be negative
- succeeded_count must not be negative
- failed_count must not be negative
- call_count must equal succeeded_count plus failed_count
- prompt_tokens must not be negative
- completion_tokens must not be negative
- total_tokens must not be negative
- total_tokens must equal prompt_tokens plus completion_tokens
- estimated_cost_usd must not be negative
- average_latency_ms must not be negative
- provider/model_name must not be blank for model-level summaries

## Cost Serialization

estimated_cost_usd is serialized as a string.

This avoids JSON floating point precision problems and preserves decimal semantics.

## Current Filters

The first version supports filtering by:

- started_at_from
- started_at_to
- provider
- model_name

The date range uses started_at because the provider call start time is the most useful timestamp for operational reporting.

## Current Limitations

The current implementation does not yet support:

- grouping by day
- grouping by tenant/workspace
- grouping by user
- cost budgets
- budget alerts
- p95/p99 latency
- failure rate percentage
- provider error category breakdown
- retry/fallback aggregation
- dashboard-ready time series
- CSV export

## Future Work

Future improvements should include:

- daily usage aggregation
- tenant/workspace attribution
- budget limits
- budget alerts
- provider/model comparison dashboards
- p95 and p99 latency
- failed call category summaries
- cost per answer
- cost per document/workspace
- reporting cache or materialized views for large datasets