# Chunk Versioning

## Purpose

Chunk versioning creates deterministic retrieval units from SectionVersion records.

A DocumentVersion stores raw document content.

A SectionVersion stores meaningful Markdown structure.

A ChunkVersion stores the smaller text unit that will later be embedded, indexed, retrieved, and cited.

## Current Flow

During local seed ingestion:

1. A Markdown document is discovered.
2. A SourceDocument is found or created.
3. A DocumentVersion is found or created.
4. SectionVersions are created if missing.
5. ChunkVersions are created for each SectionVersion if missing.
6. The ingestion run records how many chunks were created.

## ChunkVersion Fields

A ChunkVersion includes:

- section_version_id
- chunk_index
- content
- heading_context
- chunk_hash
- embedding_input_hash
- token_estimate
- risk_flags

## Chunk Hash

The chunk hash is calculated from the chunk content.

It answers:

    Did this chunk content change?

## Embedding Input Hash

The embedding input hash is calculated from:

- heading context
- chunk content

This matters because two chunks with the same body can have different meaning under different headings.

Example:

    Status: at risk

Means something different under:

    Project Atlas > Summary

Than under:

    Project Atlas > Historical Notes

## Heading Context

Heading context preserves the Markdown hierarchy around a chunk.

This improves future embedding quality and citation explainability.

## Deterministic Chunking

Chunking must be deterministic.

The same SectionVersion body and same chunking configuration should produce the same chunk contents and indexes.

Current configuration:

- target_chunk_words: 120
- max_chunk_words: 180
- overlap_words: 30

## Backfill Behavior

If a SectionVersion already exists but has no ChunkVersions, ingestion may create chunks without creating a new DocumentVersion or SectionVersion.

This supports incremental rollout of chunking after sectioning already exists.

## Current Limitations

This slice does not yet support:

- embeddings
- embedding provider reuse
- vector index entries
- semantic search
- prompt injection risk detection
- citation rendering

## Follow-Up Work

Future slices should introduce:

- EmbeddingRecord
- fake deterministic embeddings
- embedding cost tracking
- VectorIndexEntry
- semantic search with pgvector