# Database Foundation

## Purpose

This document describes the database foundation for the Incremental RAG Indexing Platform.

The foundation established SQLAlchemy, Alembic, pgvector enablement, and separate health/readiness endpoints. Domain tables for ingestion, indexing, retrieval, answers, provider calls, and evaluation now exist through later migrations.

## Responsibilities

The database foundation provides:

- SQLAlchemy engine configuration
- SQLAlchemy session factory
- declarative base for models
- Alembic migration environment
- initial migration for pgvector
- database readiness endpoint

## Health vs Readiness

The application exposes two different operational endpoints.

### Health

    GET /api/v1/health

Health confirms that the API process is alive.

It does not check the database.

### Readiness

    GET /api/v1/readiness

Readiness confirms that the application is ready to serve database-dependent workflows.

It checks:

- Postgres connectivity
- pgvector extension availability

## Why Health Does Not Check the Database

The API process can be alive even when the database is temporarily unavailable.

If health checked the database, orchestration systems could restart a healthy process due to a dependency issue.

Readiness is the correct place to check dependencies.

## Alembic Strategy

Alembic is used for schema migrations.

The first migration enables the pgvector extension:

    CREATE EXTENSION IF NOT EXISTS vector

Later migrations introduced tables for source documents, versions, embeddings, vector index entries, query traces, answers, provider calls, and evaluation results.

Dedicated audit-log tables are not part of the current repository.

## Invariants

1. Health must not depend on Postgres.
2. Readiness must fail if Postgres is unavailable.
3. Readiness must fail if pgvector is not installed.
4. Schema changes must go through Alembic migrations.

## Manual Verification

Start Postgres:

    docker compose up -d postgres

Run migrations:

    alembic upgrade head

Start the API:

    uvicorn app.main:create_app --factory --reload

Check health:

    GET /api/v1/health

Check readiness:

    GET /api/v1/readiness
