# ADR-001 PgVector Retrieval Architecture

## Status

Accepted

## Context

The platform needs semantic retrieval over versioned document chunks.

The initial system should run locally, support PostgreSQL, and avoid introducing a separate vector database before the indexing domain is proven.

## Decision

Use PostgreSQL with the pgvector extension for the first semantic retrieval implementation.

The system will store embeddings in Postgres and expose vector similarity search through the retrieval layer.

## Alternatives Considered

### External Vector Database

An external vector database could provide advanced indexing and scaling capabilities.

This option was not selected for V1 because it adds operational complexity before the core ingestion and evaluation workflows are stable.

### Keyword Search Only

Keyword search is simple and useful for exact terms.

This option was not selected as the only retrieval strategy because semantic search is required for natural language questions.

### In-Memory Vector Search

In-memory search is useful for tests and prototypes.

This option was not selected for the main implementation because it does not represent production persistence or rebuildability requirements.

## Consequences

Using pgvector keeps the architecture simple for V1.

The platform can use the same database for document versions, embeddings, query traces, and vector index entries.

The trade-off is that very large-scale vector workloads may eventually require specialized indexing strategies or a separate retrieval store.

## Rebuildability

Vector index entries are projections.

If vector index entries are deleted or corrupted, they must be rebuildable from current ChunkVersions and existing EmbeddingRecords.