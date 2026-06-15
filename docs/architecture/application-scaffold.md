# Application Scaffold

## Purpose

This document explains the initial application scaffold.

The scaffold creates the executable foundation for the Incremental RAG Indexing Platform without implementing ingestion, indexing, retrieval, or persistence logic yet.

## Current Responsibilities

The scaffold currently provides:

- FastAPI application factory
- health check endpoint
- centralized settings
- Python project configuration
- Dockerfile
- Docker Compose environment
- PostgreSQL with pgvector
- initial automated test

## Directory Structure

    app/
      api/
        routes/
      application/
      audit/
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

Application services coordinate workflows such as ingestion, indexing, retrieval, and evaluation.

They should depend on domain entities and repository interfaces.

### app/domain

Contains domain entities, value objects, enums, and invariants.

The domain layer should not depend on FastAPI, SQLAlchemy, pgvector, or provider SDKs.

### app/infrastructure

Contains infrastructure implementations.

This includes database sessions, SQLAlchemy models, repository implementations, migrations, and external system integrations.

### app/providers

Contains provider adapters.

Examples:

- FakeEmbeddingProvider
- OpenAIEmbeddingProvider
- FakeLLMProvider
- BedrockLLMProvider

Provider implementations should not leak into domain logic.

### app/retrieval

Contains retrieval-specific logic.

Examples:

- keyword search
- semantic search
- hybrid search
- scoring
- filtering
- query tracing support

### app/evaluation

Contains retrieval evaluation logic.

Examples:

- EvaluationCase
- EvaluationRun
- hit@k
- MRR

### app/audit

Contains audit logging concepts and services.

Examples:

- ingestion events
- indexing events
- retrieval events
- answer generation events
- risk flag events

### app/config

Contains application settings and configuration loading.

## Current API Boundary

The initial API boundary is:

    GET /api/v1/health

This endpoint confirms that the application process is running.

It does not check database readiness yet.

A database readiness endpoint may be added after persistence is introduced.

## Invariants

1. The application must boot without requiring a database connection.
2. The health endpoint must not perform persistence operations yet.
3. Environment-specific configuration must come from environment variables.
4. Secrets must not be committed to the repository.
5. The scaffold must preserve modular monolith boundaries.

## Follow-Up Work

Next implementation slices should add:

- database session management
- SQLAlchemy base model setup
- Alembic initialization
- domain entities for source documents
- local Markdown ingestion
- document versioning
