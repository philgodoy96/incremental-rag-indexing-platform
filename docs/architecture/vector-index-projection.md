# Vector Index Projection

## Purpose

VectorIndexEntry represents the current searchable retrieval index.

It is not an immutable historical record.

The platform keeps immutable source-of-truth records for auditability, while maintaining a mutable vector projection for efficient retrieval.

## Source of Truth

The following records are immutable or historical:

- SourceDocument
- DocumentVersion
- SectionVersion
- ChunkVersion
- EmbeddingRecord
- ChunkEmbeddingLink

These records allow the system to answer:

- What content existed at a point in time?
- Which document version produced a citation?
- Which chunk version was embedded?
- Which embedding provider and model produced a vector?
- Can we rebuild the index from stored artifacts?

## Current Projection

VectorIndexEntry is a current-state projection.

It answers:

- Which chunks are searchable right now?
- Which embedding vector should retrieval use for a logical chunk?
- Which document version does the current index point to?
- Which index entries should be ignored because they are stale?

## Logical Identity

A VectorIndexEntry is identified by:

- source_document_id
- stable_section_key
- chunk_index
- provider
- model_name

This identity allows the same logical chunk position to be updated when a new document version is created.

## Why Not Append-Only

If VectorIndexEntry were append-only, every document change would leave old vectors in the active retrieval set.

That would create problems:

- stale retrieval results
- duplicated chunks
- harder filtering
- more complex ranking
- increased storage noise

Instead, historical state remains in versioned tables, and VectorIndexEntry remains a rebuildable current projection.

## Index Update Flow

During ingestion:

1. The platform discovers source documents.
2. It creates or reuses DocumentVersion records.
3. It creates or reuses SectionVersion records.
4. It creates or reuses ChunkVersion records.
5. It creates or reuses EmbeddingRecord records.
6. It ensures ChunkEmbeddingLink exists.
7. It updates VectorIndexEntry as the current searchable projection.

## Entry Creation

A new VectorIndexEntry is created when no entry exists for the logical identity:

source_document_id + stable_section_key + chunk_index + provider + model_name

## Entry Update

An existing VectorIndexEntry is updated when the logical identity already exists but the current projection points to a different:

- document_version_id
- section_version_id
- chunk_version_id
- embedding_record_id
- embedding_input_hash
- content
- heading_context
- embedding_vector
- dimensions

## Entry Deactivation

A VectorIndexEntry is deactivated when it is active for a source document but no longer appears in the latest processed document structure.

This happens when a section or chunk is removed.

The entry remains stored for operational audit, but retrieval should ignore inactive entries.

## Idempotency

If the current projection already matches the latest processed state, the service does not update the entry and does not increment update counters.

This makes repeated ingestion of unchanged documents safe.

## Metrics

Each ingestion run tracks:

- vector_entries_created
- vector_entries_updated
- vector_entries_deactivated

These counters make indexing behavior observable.

## Current Limitations

The current implementation stores vectors through pgvector but does not yet expose semantic retrieval endpoints.

The next stage should introduce retrieval queries over active VectorIndexEntry records.

## Future Work

Future slices should add:

- pgvector similarity search repository methods
- semantic search API
- query traces
- retrieval evaluation
- grounded answer generation with citations