# Fake Provider vs Real Provider Comparison Guide

## Purpose

This guide explains how to compare the fake LLM provider with the optional OpenAI provider.

The goal is to validate that the platform behaves consistently across provider implementations while making the trade-offs visible.

## Why Compare Providers

The fake provider is useful for:

- deterministic tests
- local development without cost
- repeatable demos
- CI safety
- predictable provider behavior

The real provider is useful for:

- validating real integration behavior
- observing real latency
- observing real token usage
- validating answer quality
- validating provider error mapping
- demonstrating production-style extensibility

Both providers are valuable.

The fake provider proves the system architecture works without external dependencies.

The real provider proves the system can integrate with a production LLM provider.

## What To Compare

### Answer Quality

Compare whether each provider:

- answers the question clearly
- stays grounded in retrieved context
- avoids unsupported claims
- uses context instead of inventing details
- produces useful wording for a human reader

### Citation Quality

Compare whether each provider:

- produces an answer that matches retrieved evidence
- allows persisted citations to support the answer
- does not answer beyond cited content

### Latency

Compare:

- fake provider latency
- real provider latency
- provider call latency metadata
- end-to-end answer generation time

Expected behavior:

- fake provider should be faster and deterministic
- real provider should have network latency and more variability

### Usage and Cost

Compare:

- prompt tokens
- completion tokens
- total tokens
- estimated cost
- usage summary
- usage by model

Expected behavior:

- fake provider may produce deterministic or synthetic usage
- real provider should expose provider usage metadata when available
- usage reports should aggregate both providers consistently

### Failure Behavior

Compare:

- missing API key behavior
- invalid API key behavior
- timeout behavior
- provider failure persistence
- failed provider call read API

Expected behavior:

- fake provider should be easy to simulate
- real provider should map external failures to internal provider errors
- failed calls should remain auditable when failure happens in the answer flow

## Recommended Questions

Use the deterministic demo dataset.

Recommended questions:

    What is Project Atlas?

    Who owns Project Atlas?

    What should support do before escalating a customer issue?

    What is the incident severity process?

    What should new engineers do in their first week?

## Comparison Table Template

Use this table when recording a controlled comparison.

This table is intentionally left as a template for controlled local comparisons. Do not record provider credentials or local secrets.

| Question | Provider | Model | Latency ms | Prompt tokens | Completion tokens | Estimated cost USD | Answer grounded? | Citations relevant? | Notes |
|---|---|---|---:|---:|---:|---:|---|---|---|
| Example question | fake | fake-llm-v1 |  |  |  |  |  |  |  |
| Same example question | optional real provider | configured model |  |  |  |  |  |  |  |

## Manual Comparison Flow

### Run With Fake Provider

Set:

    LLM_PROVIDER=fake

Generate a grounded answer:

    POST /api/v1/answers

Then inspect:

    GET /api/v1/answers
    GET /api/v1/llm-provider-calls
    GET /api/v1/llm-usage/summary
    GET /api/v1/llm-usage/by-model

Record observations.

### Run With OpenAI Provider

Set:

    LLM_PROVIDER=openai
    OPENAI_API_KEY=your-local-secret

Restart the application.

Generate the same grounded answer:

    POST /api/v1/answers

Then inspect:

    GET /api/v1/answers
    GET /api/v1/llm-provider-calls
    GET /api/v1/llm-usage/summary
    GET /api/v1/llm-usage/by-model

Record observations.

Switch back afterward:

    LLM_PROVIDER=fake

## What Good Looks Like

A good comparison shows that:

- both providers use the same application boundary
- the Answer API contract does not change
- provider calls are persisted consistently
- usage reporting aggregates both provider types
- citations remain inspectable
- failures are auditable
- real provider behavior is optional and controlled

## What This Does Not Prove

A single manual comparison does not prove:

- production readiness
- model quality across all questions
- cost safety at scale
- hallucination elimination
- retrieval quality across all documents
- resilience under high concurrency

Those require additional testing, evaluation datasets, monitoring, and production hardening.

## Follow-Up Work

Future improvements should include:

- budget guardrails
- request-level provider override policy
- fallback model support
- retry and timeout strategy
- provider-specific error category reporting
- cost budget alerts
- scheduled retrieval evaluations
- baseline comparison reports