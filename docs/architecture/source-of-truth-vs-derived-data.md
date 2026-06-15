# Source of Truth vs Derived Data

## Purpose

This document defines which data must be preserved as durable truth and which data can be rebuilt.

This distinction is central to the architecture.

Without it, the system can easily become inconsistent, expensive, and difficult to audit.

## Categories

The platform separates data into five categories:

1. Source of truth
2. Derived artifacts
3. Projections
4. Operational data
5. User-facing data

## Source of Truth

Source of truth data represents durable facts about documents and their versions.

These records should be preserved for auditability, traceability, and reproducibility.

### SourceDocument

Represents a logical document from a source system.

It tracks identity across versions.

### DocumentVersion

Represents an immutable version of the full document.

It preserves raw content and checksums.

### SectionVersion

Represents an immutable structural section extracted from a document version.

It preserves section-level structure and content.

### ChunkVersion

Represents an immutable retrieval unit.

It preserves the exact text used for embeddings, retrieval, and citations.

## Why Versioned Source of Truth Matters

Immutable versions allow the system to answer:

- What did the document say when an answer was generated?
- Which chunk supported the answer?
- Did retrieval quality improve after a document update?
- Which chunks changed and required re-embedding?
- Which embeddings can be reused?
- Can we reproduce an old evaluation run?

Without immutable versions, these questions become difficult or impossible to answer.

## Derived Artifacts

Derived artifacts are generated from source of truth data.

They are not original facts, but they may be expensive to recreate.

### EmbeddingRecord

An EmbeddingRecord is derived from a ChunkVersion.

It is expensive because it may require an external provider call.

The system should avoid duplicate embeddings.

### EmbeddingCostRecord

An EmbeddingCostRecord is derived from indexing activity.

It is used for cost observability.

## Important Distinction

Derived does not always mean disposable.

Embeddings are derived, but they are expensive.

They should be preserved and reused whenever possible.

## Projections

Projections are optimized views for query performance.

### VectorIndexEntry

A VectorIndexEntry exists to support vector search.

It can be rebuilt from current ChunkVersions and EmbeddingRecords.

If the vector index is corrupted, stale, or deleted, the system should be able to rebuild it.

## Operational Data

Operational data explains what happened during system workflows.

Examples:

- IngestionRun
- IngestionJob
- QueryTrace
- AuditLogEntry
- EvaluationRun
- EvaluationResult

Some operational data is important for auditability and should be retained.

## User-Facing Data

User-facing data represents visible outputs or feedback.

Examples:

- GeneratedAnswer
- AnswerCitation
- AnswerFeedback

Generated answers should remain linked to the evidence that supported them.

## Rebuildability Rules

### Can Be Rebuilt

- VectorIndexEntry
- search projections
- derived indexes
- some cached retrieval results

### Should Be Reused When Possible

- EmbeddingRecord

### Must Be Preserved

- SourceDocument
- DocumentVersion
- SectionVersion
- ChunkVersion
- GeneratedAnswer
- AnswerCitation
- QueryTrace
- EvaluationRun
- AuditLogEntry

## Example Scenario

A document changes in one section.

The system should:

1. Create a new DocumentVersion.
2. Detect which sections changed.
3. Create new SectionVersions for changed sections.
4. Create new ChunkVersions only where chunk content changed.
5. Reuse existing EmbeddingRecords for unchanged chunks when possible.
6. Generate embeddings only for new or changed chunks.
7. Update VectorIndexEntry for current retrievable chunks.
8. Preserve old versions for auditability.

## Consequences

This approach adds implementation complexity.

However, it provides:

- auditability
- reproducible evaluation
- citation traceability
- cost control
- safer rollback
- better debugging
- better retrieval quality analysis