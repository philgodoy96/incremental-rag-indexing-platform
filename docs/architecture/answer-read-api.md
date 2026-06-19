# Answer Read API

## Purpose

The Answer Read API exposes persisted grounded answers for inspection.

Before this API, answers could be generated and persisted, but there was no way to retrieve them through the application API.

This milestone closes the basic auditability loop:

    POST /api/v1/answers
    -> returns answer_id

    GET /api/v1/answers/{answer_id}
    -> returns persisted answer and citations

## API Endpoints

### List answers

GET /api/v1/answers

Supported query parameters:

- limit
- offset
- status
- provider
- model_name

Example request:

    GET /api/v1/answers?limit=20&offset=0&status=answered

Example response:

    {
      "items": [
        {
          "id": "uuid",
          "question": "What is Project Atlas status?",
          "answer": "Project Atlas is at risk.",
          "status": "answered",
          "query_trace_id": "uuid",
          "top_k": 5,
          "provider": "fake",
          "model_name": "fake-embedding-v1",
          "created_at": "2026-06-17T00:00:00Z"
        }
      ],
      "limit": 20,
      "offset": 0
    }

### Get answer by ID

GET /api/v1/answers/{answer_id}

Example response:

    {
      "id": "uuid",
      "question": "What is Project Atlas status?",
      "answer": "Project Atlas is at risk.",
      "status": "answered",
      "query_trace_id": "uuid",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1",
      "created_at": "2026-06-17T00:00:00Z",
      "citations": [
        {
          "id": "uuid",
          "answer_id": "uuid",
          "rank": 1,
          "vector_index_entry_id": "uuid",
          "source_document_id": "uuid",
          "document_version_id": "uuid",
          "section_version_id": "uuid",
          "chunk_version_id": "uuid",
          "embedding_record_id": "uuid",
          "stable_section_key": "project-atlas-status/summary",
          "chunk_index": 0,
          "heading_context": ["Project Atlas Status", "Summary"],
          "quote": "Status: At Risk",
          "distance": 0.12,
          "created_at": "2026-06-17T00:00:00Z"
        }
      ]
    }

## What This API Is For

The Answer Read API supports inspection and debugging of generated answers.

Engineers can inspect:

- the original question
- the final answer text
- answer status
- query_trace_id
- top_k
- provider and model_name
- persisted citations
- citation ranks
- citation distances
- linked document/chunk references

## Audit Chain

A persisted answer can be traced back to retrieval and source documents:

    AnswerRecord
    -> AnswerCitationRecord
    -> query_trace_id
    -> QueryTrace
    -> QueryTraceHit
    -> ChunkVersion
    -> DocumentVersion

This makes the answer auditable after the API request completes.

## Why Answer Read API Matters

Query traces explain what retrieval did.

Answer records explain what the system actually returned to the caller.

Both are needed.

A bad answer could be caused by:

- poor retrieval
- missing source data
- stale chunks
- weak citation selection
- LLM generation issues
- insufficient context handling

The Answer Read API helps separate these failure modes.

## Validation

The list endpoint validates:

- limit must be at least 1
- limit must not exceed 100
- offset must not be negative
- provider must not be blank when provided
- model_name must not be blank when provided
- status must match a valid GroundedAnswerStatus

The detail endpoint returns 404 when the answer does not exist.

## Current Limitations

The API currently uses offset pagination.

For large production datasets, cursor pagination would be preferable.

The API does not yet support:

- tenant/workspace filtering
- date range filtering
- full-text search
- user-level authorization
- redaction of sensitive answer/citation content
- answer deletion
- retention policies

## Future Work

Future improvements should include:

- cursor pagination
- date filters
- tenant/workspace scoping
- authorization
- retention policies
- sensitive data redaction
- answer evaluation metadata
- LLM cost and token usage inspection