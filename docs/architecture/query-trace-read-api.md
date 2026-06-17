# Query Trace Read API

## Purpose

The Query Trace Read API exposes persisted semantic retrieval traces for inspection.

A retrieval trace explains what happened during a semantic search request: the query, provider, model, top_k, status, duration, result count, and retrieved chunks.

This makes the retrieval layer auditable before grounded answer generation is introduced.

## API Endpoints

### List query traces

GET /api/v1/retrieval/traces

Supported query parameters:

- limit
- offset
- status
- provider
- model_name

Example request:

    GET /api/v1/retrieval/traces?limit=20&offset=0&status=completed

Example response:

    {
      "items": [
        {
          "id": "uuid",
          "query": "What is Project Atlas status?",
          "provider": "fake",
          "model_name": "fake-embedding-v1",
          "top_k": 5,
          "status": "completed",
          "query_embedding_dimensions": 8,
          "results_count": 1,
          "started_at": "2026-06-15T00:00:00Z",
          "completed_at": "2026-06-15T00:00:00.025Z",
          "duration_ms": 25,
          "error_message": null
        }
      ],
      "limit": 20,
      "offset": 0
    }

### Get query trace by ID

GET /api/v1/retrieval/traces/{trace_id}

Example response:

    {
      "id": "uuid",
      "query": "What is Project Atlas status?",
      "provider": "fake",
      "model_name": "fake-embedding-v1",
      "top_k": 5,
      "status": "completed",
      "query_embedding_dimensions": 8,
      "results_count": 1,
      "started_at": "2026-06-15T00:00:00Z",
      "completed_at": "2026-06-15T00:00:00.025Z",
      "duration_ms": 25,
      "error_message": null,
      "hits": [
        {
          "id": "uuid",
          "query_trace_id": "uuid",
          "rank": 1,
          "vector_index_entry_id": "uuid",
          "source_document_id": "uuid",
          "document_version_id": "uuid",
          "section_version_id": "uuid",
          "chunk_version_id": "uuid",
          "embedding_record_id": "uuid",
          "stable_section_key": "project-atlas-status/summary",
          "chunk_index": 0,
          "provider": "fake",
          "model_name": "fake-embedding-v1",
          "content": "Status: At Risk",
          "heading_context": ["Project Atlas Status", "Summary"],
          "distance": 0.12,
          "created_at": "2026-06-15T00:00:00Z"
        }
      ]
    }

## What the API Is For

The API supports debugging and auditability.

Engineers can inspect:

- which query was executed
- which embedding provider and model were used
- how many results were returned
- how long retrieval took
- which chunks were retrieved
- which document versions and chunk versions were used
- what distance each retrieved chunk had
- what rank each chunk received

## Why This Matters

RAG failures can happen for many reasons:

- the source document was missing
- the document was indexed incorrectly
- chunking produced poor chunks
- embeddings were weak
- retrieval ranking was poor
- the LLM ignored good context
- the LLM hallucinated

Query traces help separate retrieval problems from answer-generation problems.

## Trace Detail

Trace detail returns hits ordered by rank.

Rank is the retrieval order returned by semantic search.

Distance is the vector distance returned by retrieval.

Lower distance means higher semantic relevance.

## Validation

The list endpoint validates:

- limit must be at least 1
- limit must not exceed 100
- offset must not be negative
- provider must not be blank when provided
- model_name must not be blank when provided
- status must match a valid QueryTraceStatus

The detail endpoint returns 404 when the trace does not exist.

## Current Limitations

The API currently provides offset pagination.

For larger production datasets, cursor pagination would be preferable.

The API does not yet support:

- tenant/workspace filtering
- date range filtering
- full-text query filtering
- trace deletion or retention workflows
- redaction of sensitive query or retrieved content

## Future Work

Future improvements should include:

- cursor pagination
- date filters
- tenant/workspace scoping
- retention policies
- failed trace persistence improvements
- integration with grounded answer traces
- operational dashboards