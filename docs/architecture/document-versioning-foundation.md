# Document Versioning Foundation

## Purpose

This document describes the first source-of-truth persistence foundation for the platform.

The goal is to represent logical source documents and immutable document versions before implementing Markdown ingestion.

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

In this slice, it is only a foundation entity.

Future slices will use it to track actual ingestion behavior.

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

This slice introduces:

    ingestion_runs
    source_documents
    document_versions

No section, chunk, embedding, retrieval, or answer tables exist yet.

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

## Follow-Up Work

Next slices should introduce:

- local Markdown source scanning
- checksum calculation
- ingestion application service
- creation of SourceDocument and DocumentVersion from files
- first seed documents