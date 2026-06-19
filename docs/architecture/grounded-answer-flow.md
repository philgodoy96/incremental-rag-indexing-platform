# Grounded Answer Flow

## Purpose

The Grounded Answer API turns semantic retrieval results into an answer with citations.

This is the API path where the platform behaves like a RAG system from an API consumer perspective.

The flow is:

1. Receive a user question.
2. Run semantic retrieval.
3. Persist a query trace.
4. Generate an answer using retrieved context.
5. Return the answer, query_trace_id, and citations.

## API Endpoint

POST /api/v1/answers

Example request:

    {
      "question": "What is Project Atlas status?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Example answered response:

    {
      "question": "What is Project Atlas status?",
      "answer": "Based on the retrieved context, Status: At Risk",
      "status": "answered",
      "query_trace_id": "uuid",
      "citations": [
        {
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
          "distance": 0.12
        }
      ]
    }

Example insufficient context response:

    {
      "question": "What is Project Phoenix budget?",
      "answer": "I do not have enough retrieved context to answer this question reliably.",
      "status": "insufficient_context",
      "query_trace_id": "uuid",
      "citations": []
    }

## Architecture

The GroundedAnswerService orchestrates the answer flow.

It depends on:

- SemanticRetriever
- LLMProvider
- RetrievalTransaction

The SemanticRetriever performs retrieval and returns retrieved chunks plus query_trace_id.

The LLMProvider generates answer text from retrieved context.

The backend creates citations from retrieved chunks.

## Why Citations Are Created by the Backend

The LLM does not create citations.

The backend creates citations using the chunks actually returned by semantic retrieval.

This prevents citation hallucination, where a model invents references that were not retrieved.

## Current Provider Strategy

The current implementation uses FakeLLMProvider.

FakeLLMProvider is deterministic and local.

This keeps tests stable and avoids API costs while the architecture is still being validated.

A real provider such as OpenAI or AWS Bedrock can be added later behind the same LLMProvider boundary.

## GroundedAnswerStatus

The answer status can be:

- answered
- insufficient_context

answered means retrieval returned context and the system generated an answer with citations.

insufficient_context means retrieval returned no chunks, so the system refused to invent an answer.

## Query Trace Integration

Every answer response includes query_trace_id.

This allows engineers to inspect the retrieval execution that supported the answer.

The query trace can be read using:

- GET /api/v1/retrieval/traces/{trace_id}

This makes the answer auditable.

## Current Limitations

The current implementation:

- persists answer records
- links answers to query traces and provider call records
- uses fake LLM provider by default and optional OpenAI LLM provider

It does not yet:

- verify whether every sentence is supported by citations
- stream responses
- support multi-turn conversations
- apply tenant/workspace filters
- enforce authorization
- redact sensitive retrieved content

## Future Work

Future hardening may add:

- citation verification
- additional LLM provider adapters
- refusal policy improvements
- evaluation for groundedness
- tenant/workspace scoping