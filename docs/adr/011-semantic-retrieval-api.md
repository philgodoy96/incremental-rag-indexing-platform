# ADR-011: Add Semantic Retrieval API Over Active Vector Index Entries

## Status

Accepted

## Context

The platform already supports document ingestion, chunking, embedding generation, embedding reuse, and current vector index projection through VectorIndexEntry.

The next required capability is to query the active vector index using natural language.

The platform should retrieve relevant chunks before generating grounded answers with an LLM.

## Decision

The system will expose a semantic retrieval API that:

- receives a natural language query
- generates a query embedding
- searches active VectorIndexEntry records
- returns top_k retrieved chunks ordered by ascending vector distance

The endpoint is:

    POST /api/v1/retrieval/search

The API returns retrieved chunks and their historical references, but it does not generate final LLM answers yet.

## Why Distance

The current implementation exposes distance rather than score.

Lower distance means higher semantic relevance.

This avoids ambiguity because score often implies that higher is better.

## Why Use VectorIndexEntry

Retrieval should query the current active retrieval projection instead of scanning historical chunk and embedding tables.

This keeps retrieval focused on current content and avoids returning stale document versions.

## Consequences

### Positive

- Enables semantic search over indexed documents.
- Keeps retrieval independent from answer generation.
- Reuses the current vector index projection.
- Returns traceable chunk references for future citations.
- Preserves clear separation between ingestion and retrieval.

### Negative

- Adds a new API surface.
- Still relies on fake embedding provider by default.
- Does not yet persist query traces.
- Does not yet generate final grounded answers.
- Requires future production vector indexing strategy for scale.

## Alternatives Considered

### Generate Answers Immediately

The system could combine retrieval and LLM answer generation in one slice.

Rejected because retrieval quality should be testable independently before answer generation.

### Search Historical Chunk Tables Directly

The system could search ChunkVersion and EmbeddingRecord tables directly.

Rejected because it risks returning stale historical chunks and couples retrieval to versioning complexity.

### Return Similarity Score Instead of Distance

The API could convert distance into a similarity score.

Deferred because conversion depends on the distance metric and may create misleading semantics.

## Follow-Up

Future work should add:

- QueryTrace persistence
- grounded answer generation
- citation formatting
- retrieval evaluation
- provider configuration for real embedding models