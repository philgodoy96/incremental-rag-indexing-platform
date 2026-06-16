# ADR-005: Use SectionVersion and Heading-Based Stable Keys

## Status

Accepted

## Context

The platform needs to move from full-document storage toward retrieval-ready structure.

DocumentVersion preserves raw content, but retrieval and citations require smaller units of evidence.

The system needs a deterministic way to identify sections across document versions.

## Decision

The system will introduce SectionVersion records.

Each SectionVersion belongs to a DocumentVersion and represents a non-empty Markdown section.

The initial stable section key strategy is based on the normalized heading path.

Example:

    Project Atlas Status > Risks > Evaluation Dataset Delay

Becomes:

    project-atlas-status/risks/evaluation-dataset-delay

## Alternatives Considered

### Use Documents Directly for Retrieval

This is simpler, but documents are too large and imprecise for grounded answers.

Rejected because citations and evaluation need smaller evidence units.

### Use Chunks Directly Without Sections

This could work for simple RAG systems.

Rejected because sections provide useful structure for incremental indexing, heading context, and future citation quality.

### Use Explicit Section IDs in Markdown

This would be more stable across renames.

Rejected for V1 because it requires authors to maintain IDs manually.

It may be added later.

## Consequences

### Positive

- Better retrieval structure
- Better future chunk context
- Section-level change detection
- More precise citation path
- Clear bridge between DocumentVersion and ChunkVersion

### Negative

- Heading renames may change stable keys
- Duplicate headings need deterministic suffixes
- Markdown parsing rules must stay deterministic
- Empty headings are not preserved as retrievable sections

## Follow-Up

Future work may improve stable section identity through:

- explicit section IDs
- content similarity
- source-provided block IDs
- rename detection