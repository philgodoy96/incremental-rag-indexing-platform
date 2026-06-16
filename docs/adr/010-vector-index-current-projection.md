# ADR-010: Use VectorIndexEntry as a Current Retrieval Projection

## Status

Accepted

## Context

The platform stores immutable document, section, chunk, and embedding artifacts.

These records are necessary for auditability, reproducibility, and citation traceability.

However, retrieval needs a current searchable index.

If retrieval queries directly scan every historical chunk and embedding, the system may return stale content from old document versions.

## Decision

The platform will use VectorIndexEntry as a mutable current projection for retrieval.

VectorIndexEntry will point to the current searchable chunk and embedding for a logical chunk identity.

The logical identity is:

- source_document_id
- stable_section_key
- chunk_index
- provider
- model_name

## Consequences

### Positive

- Keeps retrieval focused on current content.
- Avoids returning stale historical chunks.
- Preserves immutable document version history separately.
- Makes the active retrieval index rebuildable.
- Allows removed chunks to be deactivated.
- Provides clear ingestion metrics for index changes.

### Negative

- Adds another derived table to maintain.
- Requires ingestion to update projection state correctly.
- Requires careful idempotency to avoid noisy update metrics.
- Requires future concurrency protection for simultaneous ingestion runs.

## Alternatives Considered

### Query Historical Chunk Tables Directly

This would be simpler initially, but it would make stale retrieval likely unless every query carefully filters for current document versions.

Rejected because retrieval should be operationally simple and safe.

### Make VectorIndexEntry Append-Only

This would preserve every index state, but historical state is already captured by document and chunk version tables.

Rejected because it would create duplicate and stale active retrieval candidates.

### Store Only Current Chunks

This would simplify retrieval, but it would lose auditability and citation reproducibility.

Rejected because auditability is a core system requirement.

## Follow-Up

Future work should add semantic retrieval over active VectorIndexEntry records using pgvector similarity search.