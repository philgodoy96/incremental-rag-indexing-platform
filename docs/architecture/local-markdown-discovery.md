# Local Markdown Discovery

## Purpose

This document describes the local Markdown discovery foundation.

The goal is to discover local Markdown documents and calculate stable metadata before persistence.

## Source System

The source system is:

    local_seed_documents

The source directory is:

    seed_documents/

## Current Behavior

The discovery flow:

1. Scans the local seed document directory.
2. Finds Markdown files ending in `.md`.
3. Ignores non-Markdown files.
4. Ignores empty Markdown files.
5. Extracts a title from the first H1 heading.
6. Falls back to the filename when no H1 exists.
7. Calculates a content checksum.
8. Calculates a metadata checksum.
9. Returns discovered document candidates.
10. Does not persist anything.

## API Boundary

The endpoint is:

    POST /api/v1/ingestion/local-seed-documents/discover

This endpoint is a dry-run style discovery endpoint.

It does not create:

- SourceDocument
- DocumentVersion
- IngestionRun
- SectionVersion
- ChunkVersion

## SourceDocumentCandidate

A SourceDocumentCandidate represents a document found in a source system before persistence.

It includes:

- source_system
- external_id
- source_uri
- title
- raw_content
- content_checksum
- metadata_checksum

The API response intentionally excludes raw_content.

## External ID Strategy

The external id is based on the relative Markdown path from the source directory.

Examples:

    project-atlas-status.md
    runbooks/redis-queue-backlog-runbook.md
    adr/adr-001-pgvector-retrieval-architecture.md

This creates a stable identity for local source documents.

## Checksum Strategy

### Content Checksum

The content checksum is a SHA-256 hash of raw document content.

It detects content changes.

### Metadata Checksum

The metadata checksum is a SHA-256 hash of deterministic JSON metadata.

It detects metadata changes such as title or source URI changes.

## Why Discovery Does Not Persist

Discovery is intentionally separated from ingestion persistence.

This makes it possible to:

- preview source state
- test source scanning
- estimate future ingestion work
- keep scanner behavior deterministic
- avoid accidental writes during early development

## Follow-Up Work

The next slice should introduce the first real seed documents and implement a persistence-oriented ingestion service that creates:

- IngestionRun
- SourceDocument
- DocumentVersion

The system should only create new DocumentVersions when content checksums change.