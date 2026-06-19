# Application Scaffold

## Purpose

This document describes the application module layout and boundaries for the Incremental RAG Indexing Platform.

The scaffold established the executable foundation. The repository now also includes ingestion, indexing, semantic retrieval, grounded answers, provider observability, usage reporting, and retrieval evaluation. See [Project Status](../project-status.md) for the current capability list.

## Current Responsibilities

The application currently provides:

- FastAPI application factory
- health and readiness endpoints
- centralized settings
- Python project configuration
- Dockerfile and Docker Compose environment
- PostgreSQL with pgvector
- automated tests
- ingestion, indexing, retrieval, answering, evaluation, and observability APIs

## Directory Structure

    app/
      api/
        routes/
      application/
      config/
      domain/
      evaluation/
      infrastructure/
        db/
      providers/
      retrieval/
    tests/

## Module Responsibilities

### app/api

Contains HTTP routes and request/response schemas.

API modules should remain thin.

They should validate input, call application services, and return responses.

### app/application

Contains application services and use cases.

Application services coordinate workflows such as ingestion, indexing, retrieval, answering, and evaluation.

They should depend on domain entities and repository interfaces.

### app/domain

Contains domain entities, value objects, enums, and invariants.

The domain layer should not depend on FastAPI, SQLAlchemy, pgvector, or provider SDKs.

### app/infrastructure

Contains infrastructure implementations.

This includes database sessions, SQLAlchemy models, repository implementations, migrations, and external system integrations.

### app/providers

Contains provider adapters.

Implemented examples:

- FakeEmbeddingProvider
- FakeLLMProvider
- OpenAILLMProvider

Future hardening may add additional embedding and LLM providers such as Bedrock adapters behind the same boundaries.

Provider implementations should not leak into domain logic.

### app/retrieval

Contains retrieval-specific logic.

Current examples:

- semantic search
- scoring
- filtering
- query tracing support

Keyword and hybrid retrieval are not implemented in the current application surface.

### app/evaluation

Contains retrieval evaluation logic.

Examples:

- RetrievalEvaluationCase
- RetrievalEvaluationCaseResult
- hit_rate_at_k
- recall_at_k
- reciprocal_rank

### app/config

Contains application settings and configuration loading.

## Current API Boundary

The API exposes endpoints under `/api/v1`, including:

- `GET /health`
- `GET /readiness`
- ingestion, retrieval, answer, provider-call, usage-reporting, and evaluation routes

See [Project Status](../project-status.md) and [Demo API Examples](../demo/manual-flows/api-examples.md) for the current route list.

## Invariants

1. Environment-specific configuration must come from environment variables.
2. Secrets must not be committed to the repository.
3. The application preserves modular monolith boundaries.
4. Fake providers remain the default for local development and CI.
5. Real external provider usage depends on explicit configuration and local credentials.

## Recommended Next Work

Future hardening may add:

- additional embedding and LLM providers
- keyword and hybrid retrieval
- dedicated audit-log persistence
- background workers for long-running ingestion
- deployment automation and operational dashboards
