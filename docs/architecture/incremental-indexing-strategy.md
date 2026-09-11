# Incremental Indexing Strategy

## Purpose

This document explains how the platform detects changes and avoids unnecessary reprocessing.

The system should not re-embed every chunk whenever a document changes, and it should not
rechunk unchanged sections when only part of a document changes.

## Three Distinct Mechanisms

These are related but not the same:

1. **Document-level checksum no-op**
   If the full-document `content_checksum` matches the latest `DocumentVersion`, ingestion
   creates no new version and performs only backfill/idempotent ensure work.

2. **Section-level differential materialization**
   If the document checksum changed, ingestion computes a deterministic section delta using
   `stable_section_key` + `section_checksum`. Unchanged sections reuse prior immutable
   section/chunk artifacts and bypass rechunking. Modified and added sections alone are
   reprocessed. Removed sections remain historically addressable but are not members of the
   new snapshot.

3. **Chunk/embedding content reuse**
   Independently of section reuse, embedding generation looks up
   `(provider, model_name, embedding_input_hash)` and links existing `EmbeddingRecord`s when
   possible. This can apply even to newly created chunks whose content matches historical
   embedding inputs.

The implementation does **not** claim fuzzy semantic diffing, paragraph-level diffing,
exactly-once ingestion, or zero writes for reused sections (snapshot membership rows are
still created).

## Goals

The incremental indexing strategy should:

- detect source-level changes
- detect document content changes
- detect section-level changes
- detect chunk-level embedding identity matches
- avoid duplicate embeddings
- avoid rechunking unchanged sections
- support auditability
- support rollback and reproducibility

## Source System

V1 starts with local Markdown documents.

The source system name is:

    local_seed_documents

Documents live in:

    seed_documents/

Each local document has:

- external_id
- source_uri
- title
- raw content
- metadata
- content checksum
- metadata checksum

## Change Detection Levels

### 1. Source-Level Detection

The system scans the local seed document directory and compares discovered files against
known `SourceDocument` records.

### 2. Document-Level Detection

The system computes a content checksum for the full document.

If the checksum is unchanged, no new `DocumentVersion` is required.

If the checksum changed, the system creates a new `DocumentVersion` and runs section-level
differential materialization.

### 3. Metadata-Level Detection

The system computes a metadata checksum for source path/title style metadata. Content
unchanged remains the primary no-op gate for version creation.

### 4. Section-Level Detection

Markdown is parsed into sections.

Each extracted section has:

- stable_section_key
- heading_path
- heading_level
- title
- body
- section_checksum
- ordinal

`SectionDeltaPlanner` compares previous snapshot sections to incoming extracted sections by
stable key and checksum, producing:

- unchanged
- modified
- added
- removed

Ordinal movement alone does not mark a section modified when key and checksum match. The
new snapshot membership stores the incoming ordinal order.

### 5. Chunk-Level / Embedding Identity

Changed sections are chunked deterministically.

Each chunk receives:

- chunk_index
- heading_context
- content
- chunk_hash
- embedding_input_hash

If the embedding input hash already exists for the same provider and model, embedding
generation can be skipped and a link is created instead.

## Snapshot Membership vs Content Artifacts

`SectionVersion` and `ChunkVersion` are immutable content artifacts.

`document_version_sections` records membership of a `SectionVersion` in a particular
`DocumentVersion` snapshot, including ordinal.

A new document snapshot does not physically duplicate unchanged section/chunk content. It
associates existing immutable artifacts with the new version.

## Stable Section Keys

A stable section key identifies the logical section across document versions.

The V1 strategy derives the key from the normalized heading path.

Example:

    architecture/retrieval-strategy/hybrid-search

If a heading is renamed, the key may change even if the body remains similar. That appears
as remove + add under current identity rules.

## Vector Projection

Current retrieval uses active `vector_index_entries`.

After differential materialization:

- reused unchanged chunks and newly materialized changed chunks are projected for the new
  snapshot
- removed logical keys are deactivated
- projection membership is driven by the new snapshot, not artifact creation time

## Observability

Ingestion results expose differential counters such as:

- sections_unchanged
- sections_modified
- sections_added
- sections_removed
- chunks_reused
- chunks_created
- embeddings_reused
- embeddings_created

## Deletions

If a source document is removed, historical versions are retained. Current retrieval should
exclude deleted documents.

## Failure Handling

Ingestion builds the new snapshot inside the existing document ingestion transaction.
Failed ingestion must not advance the current document pointer to an incomplete snapshot.

Retries of an unchanged latest checksum remain idempotent. The platform does not claim
exactly-once execution.

## Trade-Offs

Section-level differential indexing is more complex than full rematerialization.

It improves:

- cost control
- processing efficiency
- traceability
- operational inspection of what actually changed
