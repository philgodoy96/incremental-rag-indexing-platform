# Local Seed Source Plan

## Purpose

This document describes the local seed document source used by the platform.

The source system is:

    local_seed_documents

The source directory is:

    seed_documents/

Seed documents are not placeholder content.

They are realistic documents designed to test ingestion, versioning, chunking, retrieval, citations, and evaluation.

## Initial Documents

The seed source includes documents such as:

    project-atlas-status.md
    redis-queue-backlog-runbook.md
    adr-001-pgvector-retrieval-architecture.md

The fictional Redis runbook content exercises operational-style retrieval. It does not imply that Redis-backed background workers are implemented in this repository.

## Document Purposes

### project-atlas-status.md

Tests:

- basic ingestion
- document versioning
- factual retrieval
- incremental updates
- status changes

### redis-queue-backlog-runbook.md

Tests:

- operational retrieval
- runbook-style grounded answers
- incident response questions
- section-level retrieval

### adr-001-pgvector-retrieval-architecture.md

Tests:

- architectural decision retrieval
- citation quality
- trade-off questions
- answer grounding

## Evolution Scenarios

Future hardening may intentionally modify seed documents to test incremental behavior.

Examples:

- update one status field
- rename one section
- add a new risk section
- change a runbook threshold
- add an architectural trade-off
- introduce malicious prompt-injection test content once automated detection exists

## Expected Metadata

Each local document produces metadata such as:

- source_system
- external_id
- source_uri
- title
- content_checksum
- metadata_checksum

## Related Documentation

Local Markdown discovery and ingestion behavior are documented in:

- [Local Markdown Discovery](local-markdown-discovery.md)
- [Local Seed Ingestion](local-seed-ingestion.md)
- [Initial Seed Documents](initial-seed-documents.md)
