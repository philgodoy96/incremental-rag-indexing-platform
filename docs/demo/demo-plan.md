# Demo Plan: Dataset, Seed Data & Manual Flow

## Objective

Create a reproducible end-to-end demo flow for the Incremental RAG Indexing Platform.

This demo turns the project from a strong backend and AI infrastructure implementation into a portfolio-ready demonstrable product.

## Why This Demo Exists

The project already has important backend and AI infrastructure capabilities.

However, a reviewer needs a clean way to see the system working.

This demo introduces:

- deterministic demo documents
- seed data
- retrieval evaluation cases
- manual demo flow
- Postman or cURL guide
- demo documentation

## Provider Strategy

The demo uses fake providers by default.

This keeps the project:

- free to run
- deterministic
- testable without external services
- safe for public GitHub usage

Real OpenAI integration is intentionally deferred to a separate optional provider integration.

This avoids mixing two concerns:

- reproducible local demo data and workflow
- external provider behavior and real API costs

## Planned Work

### Define end-to-end demo scenario

Create the demo scenario and plan.

### Add deterministic demo documents

Add markdown documents under the demo assets directory.

### Add demo seed data loader

Add a repeatable seed script or service to create demo records.

### Cover demo seed data validation

Add tests to ensure demo data is valid and deterministic.

### Add manual demo testing guide

Add a manual walkthrough for ingestion, retrieval, answer generation, tracing, usage reporting, and evaluation.

### Add Postman or cURL examples

Add a repeatable API testing flow for the full demo scenario.

## Future Work

Future work will add:

- optional OpenAI provider adapter
- OPENAI_API_KEY configuration
- provider selection through environment variables
- mocked tests for OpenAI adapter
- safe real-demo mode
- fake provider vs OpenAI provider comparisons
- latency observations
- token and cost observations
- answer quality observations
- citation quality observations
- retrieval evaluation observations