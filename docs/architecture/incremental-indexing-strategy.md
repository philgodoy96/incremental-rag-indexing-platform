# Incremental Indexing Strategy

## Purpose

This document explains how the platform detects changes and avoids unnecessary reprocessing.

The system should not re-embed every chunk whenever a document changes.

Only changed chunks should lead to new embedding work.

## Goals

The incremental indexing strategy should:

- detect source-level changes
- detect document content changes
- detect section-level changes
- detect chunk-level changes
- avoid duplicate embeddings
- support auditability
- support rollback and reproducibility
- estimate indexing cost before execution
- support dry runs

## Source System

V1 starts with local Markdown documents.

The source system name is:

    local_seed_documents

Documents will live in:

    seed_documents/

Each local document will have:

- external_id
- source_uri
- title
- raw content
- metadata
- content checksum
- metadata checksum

## Change Detection Levels

### 1. Source-Level Detection

The system scans the local seed document directory.

It compares discovered files against known SourceDocument records.

Possible outcomes:

- new document
- unchanged document
- changed document
- deleted document

### 2. Document-Level Detection

The system computes a content checksum for the full document.

If the checksum is unchanged, no new DocumentVersion is required.

If the checksum changed, the system creates a new DocumentVersion.

### 3. Metadata-Level Detection

The system computes a metadata checksum.

Metadata may include:

- source path
- title
- source system
- last modified time if available
- document type

Metadata changes may require dedicated audit-log persistence in future hardening even when content is unchanged.

### 4. Section-Level Detection

Markdown is parsed into sections.

Each section receives:

- stable_section_key
- heading_path
- heading_level
- title
- body
- section_checksum
- ordinal

The section checksum helps identify changed content.

### 5. Chunk-Level Detection

Each section is chunked deterministically.

Each chunk receives:

- chunk_index
- heading_context
- content
- chunk_hash
- embedding_input_hash

If the embedding input hash already exists for the same provider, model, and dimension, embedding generation can be skipped.

## Stable Section Keys

A stable section key should help identify the logical section across document versions.

A simple initial strategy may derive the key from normalized heading path.

Example:

    architecture/retrieval-strategy/hybrid-search

This is not perfect.

If a heading is renamed, the key may change even if the body remains similar.

Future versions may improve this with content similarity or explicit section identifiers.

## Chunking Rules

Chunking should be deterministic.

Inputs:

- section body
- heading context
- target_chunk_words
- max_chunk_words
- overlap_words

The same section content and same chunking parameters should produce the same chunks.

## Embedding Identity

The system should treat an embedding as uniquely identified by:

    chunk_version_id + provider + model + dimension + embedding_input_hash

Before calling a provider, the system checks if this embedding already exists.

If it exists, the system reuses it.

If not, the system creates it.

## Dry Run

Indexing should support dry runs.

A dry run should report:

- documents discovered
- changed documents
- estimated sections
- estimated chunks
- chunks requiring embedding
- estimated tokens
- estimated cost

A dry run must not mutate durable indexing state.

## Max Chunks and Max Cost

The system should support safety controls:

- max_chunks
- max_cost

If a run exceeds configured limits, it should stop before expensive provider calls.

## Deletions

If a source document is removed, the system should not physically delete historical versions.

Instead, the SourceDocument may be marked deleted.

Current retrieval should exclude deleted documents.

Historical answers and evaluation runs should remain reproducible.

## Failure Handling

### Provider Failure

If embedding generation fails, the system should:

- record the failure
- avoid marking the chunk as indexed
- allow safe retry

### Partial Indexing Failure

If some chunks are indexed and others fail, the system should preserve successful work and allow retry for missing work.

### Process Crash

If ingestion crashes mid-run, the next run should detect already completed work and avoid duplication.

## Audit Events

Future hardening may emit dedicated audit events for:

- ingestion started
- ingestion completed
- document discovered
- document version created
- section version created
- chunk version created
- embedding reused
- embedding created
- vector index updated
- indexing failed
- prompt injection risk detected

Today, important workflow state is persisted through ingestion runs, version records, query traces, answers, provider calls, and evaluation results rather than a separate audit-log service.

## Trade-Offs

This strategy is more complex than full re-indexing.

However, it improves:

- cost control
- traceability
- auditability
- reliability
- retrieval evaluation
- operational inspection before wider deployment