# ADR-024: Section-Level Differential Materialization Across Document Versions

## Status

Accepted

## Context

Document-level checksum idempotency already skips work when an entire document is unchanged.
Cross-version embedding reuse already avoids provider calls when `embedding_input_hash` matches.

However, when any part of a document changed, ingestion still rematerialized every
`SectionVersion` and `ChunkVersion` under the new `DocumentVersion`. Unchanged sections
were duplicated as new content rows and rechunked even though their content identity was
identical.

The data model also conflated immutable section content with snapshot membership by
requiring `SectionVersion.document_version_id`, which forced one content row per document
version.

## Decision

When a document checksum changes, ingestion computes a deterministic section delta between
the latest persisted snapshot and the newly extracted sections.

Classification uses:

- stable identity: `stable_section_key`
- content identity: `section_checksum`

Delta classes:

- `UNCHANGED` — same key and checksum
- `MODIFIED` — same key, different checksum
- `ADDED` — key present only in the incoming document
- `REMOVED` — key present only in the previous snapshot

Processing rules:

- `UNCHANGED`: reuse the existing immutable `SectionVersion` and its `ChunkVersion` rows;
  create only a new snapshot membership row for the new `DocumentVersion`; do not rechunk;
  do not call the embedding provider for already-linked unchanged chunks.
- `MODIFIED` / `ADDED`: materialize a new `SectionVersion`, chunk that section only, then
  resolve embeddings with existing `embedding_input_hash` reuse rules.
- `REMOVED`: omit from the new snapshot membership; keep historical membership and artifacts;
  current vector projection deactivates removed logical keys.

Schema change:

- Introduce `document_version_sections` as the membership association between
  `DocumentVersion` and reusable `SectionVersion` content artifacts.
- Remove `document_version_id` and `ordinal` from `section_versions`; ordinal becomes a
  snapshot membership property so reordering without content change remains `UNCHANGED`.

Document-level checksum no-op remains the fast path and still skips new `DocumentVersion`
creation.

## Alternatives Considered

### Rebuild every changed document snapshot

Always rematerialize all sections and chunks for a new document version.

Rejected because it wastes CPU on unchanged sections and falsely implies every section
changed.

### Rebuild structural artifacts but reuse embeddings only

Still create new section/chunk rows for unchanged content, relying only on embedding hash
reuse.

Rejected because it avoids provider cost but still rechunks and duplicates immutable
content, which obscures true differential indexing.

### Section-level differential materialization

Chosen. It matches the platform thesis: reprocess only affected sections while preserving
immutable history and snapshot completeness.

### Finer-grained paragraph/chunk diffing

Could reduce work further for large sections with small edits.

Rejected for this PR because stable section identity already exists, section checksums are
deterministic, and paragraph-level matching would add fuzzy or brittle identity rules.

## Consequences

### Positive

- Unchanged sections skip chunking and avoid unnecessary embedding generation
- New document snapshots remain complete and immutable at the membership layer
- Historical snapshots remain queryable through prior membership rows
- Vector projection continues to derive active membership from the current snapshot
- Operational counters expose section/chunk reuse behavior

### Negative

- Membership writes still occur for reused sections in a new snapshot
- Heading renames still appear as remove + add under stable key semantics
- Migration `20260618_0013` is **explicitly irreversible**

  After upgrade, one `SectionVersion` content row may belong to multiple document
  snapshots through `document_version_sections`. The previous schema required one
  section row per `DocumentVersion`. Restoring that shape would require cloning
  shared sections/chunks and remapping embedding links, vector-index foreign keys,
  denormalized citation/query-trace identifiers, and evaluation chunk-id lists.
  That rematerialization is disproportionate and unsafe to embed in a silent
  Alembic downgrade.

  Operational rollback strategy:

  - restore from a backup taken before `alembic upgrade` to this revision; or
  - apply a dedicated roll-forward recovery migration if one is authored later

  Do not describe this revision as generally downgrade-safe. `alembic downgrade`
  for this revision fails loudly before any destructive schema or data mutation.

## Revisit Triggers

- Need for finer than section-level edit detection
- Section identity instability under heading renames
- Very large documents where membership-row write amplification becomes material
- Collaborative or streaming document mutation models that invalidate whole-document
  snapshot planning
