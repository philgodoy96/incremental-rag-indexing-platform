# Local Seed Ingestion

## Purpose

Local seed ingestion persists Markdown documents from the local source directory into source-of-truth document records.

The source system is:

    local_seed_documents

The source directory is:

    seed_documents/

## Current Behavior

The ingestion endpoint:

    POST /api/v1/ingestion/local-seed-documents/runs

Performs these steps:

1. Starts an IngestionRun.
2. Discovers local Markdown documents.
3. Finds or creates SourceDocument records.
4. Creates a DocumentVersion for new documents.
5. Reuses the latest DocumentVersion when content is unchanged.
6. Creates a new DocumentVersion when content checksum changes.
7. Updates SourceDocument.current_document_version_id.
8. Marks the IngestionRun as completed.
9. Commits the transaction.

## Idempotency

Re-running ingestion without changing documents should not create new DocumentVersions.

The system compares the discovered content checksum against the latest DocumentVersion content checksum.

If the checksum is unchanged, the document is marked as unchanged for that run.

## Current Limitations

This slice does not yet support:

- section extraction
- chunking
- embeddings
- vector indexing
- audit logs
- deletion detection
- concurrency protection for simultaneous ingestion runs

## Transaction Boundary

The ingestion service depends on a transaction abstraction.

The SQLAlchemy implementation provides:

- source document repository
- document version repository
- ingestion run repository
- commit
- rollback

This keeps the application service independent from direct SQLAlchemy session usage.

## Follow-Up Work

Future slices should add:

- SectionVersion
- Markdown section extraction
- section-level checksums
- ChunkVersion
- deterministic chunking
- embedding generation for changed chunks only