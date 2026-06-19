# Answer Persistence

## Purpose

Answer persistence stores the final grounded answer returned by the system.

Before this milestone, the platform persisted retrieval traces, but the final answer only existed in the API response.

This document describes durable answer records so generated answers can be audited after the request completes.

## Why This Matters

A production RAG platform needs to answer questions such as:

- What question was asked?
- What answer did the system return?
- Which query_trace_id supported the answer?
- Which citations were returned?
- Which provider and model were used?
- Was the answer answered or insufficient_context?
- When was the answer created?

Without answer persistence, the platform can inspect retrieval behavior but cannot inspect the final product delivered to the caller.

## Data Model

Answer persistence introduces two records:

- AnswerRecord
- AnswerCitationRecord

## AnswerRecord

AnswerRecord stores request-level and answer-level metadata.

It includes:

- id
- question
- answer
- status
- query_trace_id
- top_k
- provider
- model_name
- created_at

## AnswerCitationRecord

AnswerCitationRecord stores persisted citation metadata for an answer.

It includes:

- id
- answer_id
- rank
- vector_index_entry_id
- source_document_id
- document_version_id
- section_version_id
- chunk_version_id
- embedding_record_id
- stable_section_key
- chunk_index
- heading_context
- quote
- distance
- created_at

## Audit Chain

Answer persistence creates a durable audit chain:

    AnswerRecord
    -> query_trace_id
    -> QueryTrace
    -> QueryTraceHit
    -> ChunkVersion
    -> DocumentVersion

This makes it possible to inspect both the answer and the retrieval execution that supported it.

## Transaction Boundary

Answer persistence uses AnsweringTransaction.

AnsweringTransaction extends RetrievalTransaction with answer repositories.

This allows the answer service to use the same database transaction for:

- retrieval tracing
- answer persistence
- citation persistence

## API Behavior

The Grounded Answer API now returns answer_id.

Endpoint:

    POST /api/v1/answers

Response includes:

    {
      "answer_id": "uuid",
      "question": "What is Project Atlas status?",
      "answer": "Based on the retrieved context, Status: At Risk",
      "status": "answered",
      "query_trace_id": "uuid",
      "citations": []
    }

The answer_id can later be used to inspect the persisted answer.

## Current Limitations

Answer read APIs are available at:

- GET /api/v1/answers
- GET /api/v1/answers/{answer_id}

LLM provider calls, token usage metadata, estimated cost, and latency are persisted through LLMProviderCallRecord and exposed through provider-call and usage-reporting APIs.

The platform does not yet track:

- prompt template version
- citation verification status
- answer-level evaluation metrics
- tenant/workspace scoping

## Future Work

Future hardening may add:

- prompt version tracking
- answer trace records
- citation verification
- groundedness evaluation
- tenant/workspace scoping
- retention policies