# Database Foundation

## Purpose

This document describes the initial database foundation for the Incremental RAG Indexing Platform.

The goal of this slice is to prepare the application for persistence without introducing domain tables yet.

## Responsibilities

The database foundation provides:

- SQLAlchemy engine configuration
- SQLAlchemy session factory
- declarative base for future models
- Alembic migration environment
- initial migration for pgvector
- database readiness endpoint

## Non-Responsibilities

This slice does not introduce:

- source document tables
- document version tables
- section version tables
- chunk version tables
- embedding tables
- repository implementations
- domain persistence logic

Those belong to later slices.

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

Future migrations will introduce tables for:

- source documents
- document versions
- section versions
- chunk versions
- embeddings
- vector index entries
- ingestion runs
- query traces
- audit logs
- evaluation runs

## Invariants

1. The application must be able to boot without opening a database connection.
2. Health must not depend on Postgres.
3. Readiness must fail if Postgres is unavailable.
4. Readiness must fail if pgvector is not installed.
5. Schema changes must go through Alembic migrations.
6. Domain tables should not be added before the domain slice.

## Manual Verification

Start Postgres:

    docker compose up -d postgres

Run migrations:

    alembic upgrade head

Start the API:

    uvicorn app.main:app --reload

Check health:

    GET /api/v1/health

Check readiness:

    GET /api/v1/readiness