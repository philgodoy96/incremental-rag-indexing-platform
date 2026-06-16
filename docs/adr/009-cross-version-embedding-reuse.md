# ADR-009: Reuse Embeddings Across Chunk Versions

## Status

Accepted

## Context

The platform stores immutable document versions and derived chunk versions.

A document can change slightly while most of its sections and chunks remain semantically identical.

If embeddings are tied only to ChunkVersion IDs, the system may regenerate embeddings unnecessarily whenever a new DocumentVersion creates new ChunkVersion records.

This conflicts with the project goal of incremental indexing.

## Decision

The system will reuse embeddings across chunk versions when the semantic embedding input is identical.

Embedding identity is based on:

- provider
- model_name
- embedding_input_hash

A new ChunkEmbeddingLink connects each ChunkVersion to the selected EmbeddingRecord.

## Consequences

### Positive

- Reduces unnecessary embedding provider calls.
- Reduces estimated indexing cost.
- Improves ingestion efficiency.
- Preserves immutable document version history.
- Enables backfilling links without regenerating vectors.
- Prepares the system for rebuildable vector index projections.

### Negative

- Adds an extra association table.
- Makes embedding persistence slightly more complex.
- Requires careful distinction between embedding creation and embedding reuse.
- The current model still keeps chunk_version_id on EmbeddingRecord for traceability.

## Alternatives Considered

### Tie Embeddings Only to ChunkVersion

This is simpler, but it causes unnecessary re-embedding when unchanged chunks appear in newer document versions.

Rejected because it weakens incremental indexing.

### Remove DocumentVersion

This would reduce versioning complexity, but it would harm auditability, reproducibility, and citation traceability.

Rejected because document versioning is part of the platform source of truth.

### Fully Normalize EmbeddingRecord Immediately

A cleaner model would remove chunk_version_id from EmbeddingRecord and rely only on ChunkEmbeddingLink.

Deferred because the current design provides most of the benefit without a large migration.

## Follow-Up

Future work should introduce a VectorIndexEntry projection that represents the current retrievable index.

That projection should be mutable and rebuildable, while document and chunk versions remain immutable.