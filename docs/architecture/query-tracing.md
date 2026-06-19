# Query Tracing

## Purpose

Query tracing records what happened during a semantic retrieval request.

A RAG system should not be a black box. When retrieval quality is poor, engineers need to inspect what query was executed, which model was used, which chunks were retrieved, in what order, and with which distances.

QueryTrace and QueryTraceHit provide that audit trail.

## Problem

Without query tracing, it is hard to answer questions such as:

- Did retrieval return the right chunks?
- Did the embedding model produce useful results?
- Were results ordered correctly?
- Was the issue caused by retrieval or by the LLM answer generation layer?
- Which document versions were used to support a future answer?

## Current Flow

The semantic retrieval flow is now:

1. Receive a semantic search request.
2. Create a QueryTrace with STARTED status.
3. Generate the query embedding.
4. Search active VectorIndexEntry records.
5. Persist one QueryTraceHit for each retrieved chunk.
6. Mark the QueryTrace as COMPLETED.
7. Return retrieved chunks and query_trace_id to the API caller.

## QueryTrace

QueryTrace represents one semantic retrieval execution.

It stores:

- query
- provider
- model_name
- top_k
- status
- query_embedding_dimensions
- results_count
- started_at
- completed_at
- duration_ms
- error_message

The current implementation persists completed traces.

The domain model already supports FAILED traces, but full failure persistence is deferred.

## QueryTraceHit

QueryTraceHit represents one retrieved chunk inside a trace.

It stores:

- query_trace_id
- rank
- vector_index_entry_id
- source_document_id
- document_version_id
- section_version_id
- chunk_version_id
- embedding_record_id
- stable_section_key
- chunk_index
- content
- heading_context
- distance

The rank preserves the retrieval order.

The distance preserves the retrieval score semantics.

Lower distance means higher semantic relevance.

## Why Store Hits Separately

QueryTrace stores the request-level metadata.

QueryTraceHit stores result-level metadata.

This separation allows the system to:

- inspect all hits for a query
- compare ranking positions
- debug bad retrieval results
- support future evaluation datasets
- connect answer citations back to retrieved chunks

## API Behavior

The semantic retrieval API returns query_trace_id.

This allows future debugging workflows such as:

- retrieve the trace by ID
- inspect all retrieved chunks
- inspect ranking and distance
- compare retrieval against generated answers

## Current Limitations

Query trace read APIs are available at:

- GET /api/v1/retrieval/traces
- GET /api/v1/retrieval/traces/{trace_id}

Future hardening may add:

- failed trace persistence across all failure modes
- pagination improvements such as cursor pagination
- filtering by provider, model, status, and date
- retention policies for old traces

## Operational Notes

Query traces can grow quickly in production.

A real deployment should consider:

- retention windows
- tenant/workspace partitioning
- pagination
- database indexes
- privacy/security review for stored query text and content snapshots