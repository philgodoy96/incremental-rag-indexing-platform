# Document Versioning Foundation

## Purpose

This document describes the source-of-truth persistence foundation for logical documents and immutable document versions.

The repository now also includes section versions, chunk versions, embeddings, vector index entries, retrieval, answers, and evaluation. This document focuses on the document-version foundation that those later capabilities build on.

## Core Concepts

### SourceDocument

A SourceDocument represents the logical identity of a document from a source system.

For local Markdown files, examples include:

    project-atlas-status.md
    redis-queue-backlog-runbook.md
    adr-001-pgvector-retrieval-architecture.md

The SourceDocument survives across content changes.

It points to the current DocumentVersion through:

    current_document_version_id

### DocumentVersion

A DocumentVersion represents an immutable snapshot of a document's raw content and checksums.

When content changes, the system creates a new DocumentVersion instead of overwriting the old one.

### IngestionRun

An IngestionRun represents one execution of a source scanning or ingestion workflow.

Ingestion runs track how source-of-truth records were created or updated.

## Source of Truth

The following are source-of-truth records:

- SourceDocument
- DocumentVersion

IngestionRun is operational data that explains how source-of-truth records were created.

## Why Versions Are Immutable

Immutable versions allow the system to answer:

- What did the document say at the time an answer was generated?
- Which version introduced a change?
- Which chunks came from which document version?
- Can an old evaluation run be reproduced?
- Can citations continue to point to historical evidence?

## Database Tables

The document foundation introduced:

    ingestion_runs
    source_documents
    document_versions

Later migrations added section, chunk, embedding, retrieval, answer, provider-call, and evaluation tables.

## Current Version Pointer

The SourceDocument table contains:

    current_document_version_id

This allows normal retrieval workflows to use only current document versions.

Historical versions remain available for:

- auditability
- evaluation reproducibility
- answer traceability
- debugging
- rollback analysis

## Domain vs Database Model

Domain entities live in:

    app/domain/documents/

SQLAlchemy models live in:

    app/infrastructure/db/models/

Mapping lives in:

    app/infrastructure/db/mappers/

This explicit mapping is intentional.

The application should not treat SQLAlchemy models as domain entities.

## Related Documentation

- [Local Seed Ingestion](local-seed-ingestion.md)
- [Section Versioning](section-versioning.md)
- [Chunk Versioning](chunk-versioning.md)
