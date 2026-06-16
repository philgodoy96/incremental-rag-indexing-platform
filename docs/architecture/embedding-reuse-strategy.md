# Embedding Reuse Strategy

## Purpose

The platform should avoid generating new embeddings when the semantic embedding input has not changed.

A new DocumentVersion may be created because the document changed somewhere, but unchanged chunks should not require new provider calls.

This is central to the project thesis: incremental RAG indexing.

## Problem

If embedding records are identified only by ChunkVersion ID, then every new ChunkVersion may trigger a new embedding, even when the content and heading context are identical to a previous version.

That behavior is inefficient because it increases:

- embedding provider calls
- indexing cost
- ingestion latency
- duplicate vectors
- operational noise

## Decision

The system separates embedding identity from chunk version identity.

Embedding identity is based on:

- provider
- model_name
- embedding_input_hash

Chunk usage is represented through ChunkEmbeddingLink.

## Current Model

EmbeddingRecord represents the vector generated for a semantic input.

ChunkEmbeddingLink connects a ChunkVersion to an EmbeddingRecord.

This allows multiple ChunkVersions to reuse the same EmbeddingRecord when their embedding input is identical.

## Flow

For each ChunkVersion:

1. Check whether the chunk already has a ChunkEmbeddingLink.
2. If a link exists, do nothing.
3. If no link exists, search for an EmbeddingRecord by provider, model, and embedding_input_hash.
4. If an EmbeddingRecord exists, create only a ChunkEmbeddingLink and count the embedding as reused.
5. If no EmbeddingRecord exists, call the embedding provider, create an EmbeddingRecord, create a ChunkEmbeddingLink, and create an EmbeddingCostRecord.

## What Counts as Reuse

Reuse happens when two chunks have the same:

- provider
- model_name
- embedding_input_hash

The ChunkVersion IDs may be different.

This allows reuse across document versions.

## What Does Not Count as Reuse

If the chunk content or heading context changes, the embedding_input_hash changes.

In that case, the system must generate a new embedding.

## Why Keep DocumentVersion

DocumentVersion remains important for auditability and reproducibility.

It answers:

- What was the full document content at this point in time?
- Which document version produced a citation?
- What changed between versions?
- Can we rebuild sections, chunks, embeddings, and indexes from source data?

Embedding reuse optimizes provider usage, but it does not replace document versioning.

## Source of Truth vs Derived Data

Source-of-truth records:

- SourceDocument
- DocumentVersion
- SectionVersion
- ChunkVersion

Reusable embedding data:

- EmbeddingRecord

Association data:

- ChunkEmbeddingLink

Operational cost data:

- EmbeddingCostRecord

## Invariants

- A ChunkVersion should have at most one ChunkEmbeddingLink.
- An EmbeddingRecord may be reused by multiple ChunkVersions.
- EmbeddingCostRecord should only be created when a new EmbeddingRecord is created.
- Reused embeddings should not increase embedding token processing cost.
- Same provider, model, and embedding_input_hash should not require a new provider call.

## Current Limitations

The current implementation still stores chunk_version_id on EmbeddingRecord for traceability.

A more normalized future model could remove chunk_version_id from EmbeddingRecord and use ChunkEmbeddingLink as the only chunk association.

This was intentionally deferred to avoid over-expanding this slice.

## Future Work

Future slices should introduce:

- VectorIndexEntry
- current vector index projection
- pgvector-backed retrieval
- active/inactive vector entries
- semantic retrieval endpoint
- retrieval traces
- grounded citations