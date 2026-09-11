# Section Versioning

## Purpose

Section versioning creates a structured representation of Markdown content for retrieval
and differential indexing.

A `DocumentVersion` stores the full raw document snapshot.

A `SectionVersion` stores one immutable non-empty Markdown section content artifact.

Snapshot membership is recorded separately in `document_version_sections`, so unchanged
section content can be reused across document versions without duplication.

## Current Flow

During local seed ingestion:

1. A Markdown document is discovered.
2. A `SourceDocument` is found or created.
3. A `DocumentVersion` is found or created from the document checksum gate.
4. Markdown sections are extracted from the document raw content.
5. If this is a new document version, `SectionDeltaPlanner` classifies each section as
   unchanged, modified, added, or removed relative to the previous snapshot.
6. Unchanged sections are associated with the new snapshot via membership rows only.
7. Modified and added sections receive new `SectionVersion` content rows and are chunked.
8. Removed sections keep historical membership but are absent from the new snapshot.

## Why SectionVersion Exists

Document-level retrieval is too coarse.

Retrieval and citations need smaller evidence units than an entire document.

`SectionVersion` is the intermediate immutable content layer before `ChunkVersion`, and the
unit of differential materialization.

## Content vs Membership

`SectionVersion` content fields:

- stable_section_key
- heading_path
- heading_level
- title
- body
- section_checksum
- created_at

`document_version_sections` membership fields:

- document_version_id
- section_version_id
- ordinal

Domain code hydrates `SectionVersion.document_version_id` and `ordinal` when listing
sections for a specific snapshot.

## Stable Section Key

The stable section key is derived from the normalized heading path.

Example:

    Redis Queue Backlog Runbook > Initial Triage

Becomes:

    redis-queue-backlog-runbook/initial-triage

If the same heading path appears multiple times, deterministic suffixes are added:

    runbook/notes
    runbook/notes--2

## Section Checksum

The section checksum is calculated from:

- heading path
- section body

A section is `UNCHANGED` across versions only when both `stable_section_key` and
`section_checksum` match.

## Empty Sections

Empty sections are ignored.

A heading with no body does not become a `SectionVersion`.

## Backfill Behavior

If a `DocumentVersion` already exists but has no section memberships, ingestion may create
sections for it without creating a new `DocumentVersion`.

## Current Limitations

The current implementation does not yet support:

- fuzzy section rename detection beyond heading-path keys
- paragraph-level differential indexing inside a section
- citation generation at section level as a first-class API
- automated prompt injection risk detection

## Follow-Up Work

Future hardening may add:

- richer section rename detection
- finer-grained edit detection inside large sections
- prompt injection risk detection
