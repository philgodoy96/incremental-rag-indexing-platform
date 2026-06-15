# Local Seed Source Plan

## Purpose

This document describes the planned local seed document source.

The first source system is:

    local_seed_documents

The source directory will be:

    seed_documents/

Seed documents are not placeholder content.

They are realistic documents designed to test ingestion, versioning, chunking, retrieval, citations, evaluation, and prompt injection detection.

## Planned Initial Documents

The first documents will be introduced only when ingestion logic exists.

Planned files include:

    project-atlas-status.md
    redis-queue-backlog-runbook.md
    adr-001-pgvector-retrieval-architecture.md

## Why Documents Are Introduced Gradually

Documents should be added when the system can process them meaningfully.

Adding all documents before ingestion exists would create static sample content without engineering value.

The goal is to connect each document to a system behavior.

## Planned Document Purposes

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

## Planned Evolution Scenarios

Later slices will intentionally modify seed documents to test incremental behavior.

Examples:

- update one status field
- rename one section
- add a new risk section
- change a runbook threshold
- add an architectural trade-off
- introduce a malicious prompt injection pattern

## Expected Metadata

Each local document should eventually produce metadata such as:

- source_system
- external_id
- source_uri
- title
- content_checksum
- metadata_checksum

## Follow-Up Work

The next slice should implement a local Markdown scanner capable of discovering files and producing source document candidates without persisting them yet.