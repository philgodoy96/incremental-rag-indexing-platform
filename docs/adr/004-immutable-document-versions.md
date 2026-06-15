# ADR-004: Use Immutable Document Versions

## Status

Accepted

## Context

The platform needs to preserve document history for auditability, citations, evaluation, and incremental indexing.

A simpler design could store only the latest document content in a single row.

That would reduce storage and implementation complexity, but it would make historical traceability much weaker.

## Decision

The system will represent document content using immutable DocumentVersion records.

When document content changes, the system creates a new DocumentVersion.

The previous version remains stored.

The SourceDocument points to the current version through:

    current_document_version_id

## Alternatives Considered

### Overwrite Current Document Content

This is simpler and common in CRUD systems.

Rejected because it makes it difficult to reproduce old answers, old evaluation runs, and historical citations.

### Store Only Diffs

This could reduce storage usage.

Rejected for V1 because it adds complexity before the core indexing workflow is proven.

Full snapshots are easier to reason about and test.

### Store Versions Only in Object Storage

This may make sense at larger scale.

Rejected for V1 because local development and query traceability are simpler when versions are directly available in Postgres.

## Consequences

### Positive

- Strong auditability
- Reproducible evaluations
- Historical citation support
- Easier rollback analysis
- Clear incremental indexing boundary
- Easier debugging of retrieval regressions

### Negative

- More storage usage
- More tables and relationships
- More complex ingestion workflow
- Requires careful current-version filtering during retrieval

## Follow-Up

Future slices will add:

- SectionVersion
- ChunkVersion
- embedding reuse
- current-version retrieval filtering
- evaluation against specific document versions