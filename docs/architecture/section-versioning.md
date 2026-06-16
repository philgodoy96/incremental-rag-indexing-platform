# Section Versioning

## Purpose

Section versioning creates a structured representation of a Markdown DocumentVersion.

A DocumentVersion stores the full raw document.

A SectionVersion stores one meaningful section extracted from that document.

## Current Flow

During local seed ingestion:

1. A Markdown document is discovered.
2. A SourceDocument is found or created.
3. A DocumentVersion is found or created.
4. Markdown sections are extracted from the DocumentVersion raw content.
5. SectionVersion records are created if they do not already exist for that DocumentVersion.

## Why SectionVersion Exists

Document-level retrieval is too coarse.

Future retrieval should return evidence at a smaller unit than an entire document.

SectionVersion is the intermediate source-of-truth layer before ChunkVersion.

## Section Fields

A SectionVersion includes:

- document_version_id
- stable_section_key
- heading_path
- heading_level
- title
- body
- section_checksum
- ordinal

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

This allows future incremental indexing logic to detect section-level changes.

## Empty Sections

Empty sections are ignored.

A heading with no body does not become a SectionVersion.

This avoids storing structural headings that have no retrievable content.

## Backfill Behavior

If a DocumentVersion already exists but has no SectionVersions, ingestion may create sections for it without creating a new DocumentVersion.

This supports forward migration of existing ingested documents after sectioning is introduced.

## Current Limitations

This slice does not yet support:

- ChunkVersion
- chunk overlap
- embeddings
- semantic search
- citation generation
- section rename detection beyond heading-path keys

## Follow-Up Work

Next slices should introduce:

- deterministic chunking
- ChunkVersion
- chunk hashes
- embedding input hashes
- changed-section-only chunk generation