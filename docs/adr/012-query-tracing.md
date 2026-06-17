# ADR-012: Persist Query Traces for Semantic Retrieval

## Status

Accepted

## Context

The platform now supports semantic retrieval over active VectorIndexEntry records.

However, retrieval results need to be inspectable.

In production RAG systems, bad answers can come from several causes:

- missing source documents
- stale index entries
- poor chunking
- poor embeddings
- weak retrieval ranking
- hallucination during answer generation

Without query traces, it is difficult to determine whether the retrieval layer behaved correctly.

## Decision

The system will persist QueryTrace and QueryTraceHit records for semantic retrieval.

QueryTrace stores request-level metadata.

QueryTraceHit stores retrieved chunk metadata, rank, and distance.

The semantic retrieval API will return query_trace_id so future systems can inspect the retrieval execution.

## Consequences

### Positive

- Improves retrieval observability.
- Supports debugging bad RAG outputs.
- Preserves retrieved chunk order and distance.
- Enables future evaluation workflows.
- Prepares grounded answer generation for citation traceability.

### Negative

- Adds additional persistence writes during retrieval.
- Increases database storage usage.
- Requires future retention and pagination strategy.
- Stores user queries and retrieved content snapshots, which may require privacy review.

## Alternatives Considered

### Do Not Persist Retrieval Traces

This would keep retrieval simpler, but it would make debugging and evaluation much harder.

Rejected because observability is a core requirement for reliable RAG systems.

### Only Log Retrieval Events

Structured logs are useful, but they are not ideal for product-level inspection, evaluation, or trace-linked answer generation.

Rejected because query traces need to be queryable as domain data.

### Store Hits Inside QueryTrace JSON

This would reduce table count, but it would make ranking inspection, filtering, pagination, and future analytics harder.

Rejected in favor of a normalized QueryTraceHit table.

## Follow-Up

Future work should add:

- trace reading endpoints
- failed trace persistence
- retrieval evaluation
- answer generation linked to query_trace_id
- retention policies
- tenant/workspace scoping