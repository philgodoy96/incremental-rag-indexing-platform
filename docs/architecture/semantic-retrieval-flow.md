# Semantic Retrieval Flow

## Purpose

Semantic retrieval allows users to search indexed documents using natural language.

This slice does not generate final LLM answers. It only retrieves the most semantically relevant chunks from the active vector index.

## Flow

The retrieval flow is:

1. Receive a textual query.
2. Validate query input.
3. Generate an embedding for the query.
4. Search active VectorIndexEntry records by vector distance.
5. Return the top_k retrieved chunks ordered by ascending distance.

## API

Endpoint:

    POST /api/v1/retrieval/search

Example request:

    {
      "query": "What is the current status of Project Atlas?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Example response:

    {
      "query": "What is the current status of Project Atlas?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1",
      "results": [
        {
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
          "distance": 0.12
        }
      ]
    }

## Distance Semantics

The current implementation uses vector distance.

Lower distance means higher semantic relevance.

Results should be ordered by distance ascending.

This is intentionally exposed as distance instead of score because score often implies that higher is better.

## Active Index Only

Retrieval must query only active VectorIndexEntry records.

Historical chunks remain available through versioned tables, but retrieval should not return stale chunks from old document versions.

## Why Retrieval Uses VectorIndexEntry

VectorIndexEntry is the current retrieval projection.

It contains the active searchable chunk, embedding vector, provider, model, and references back to historical source-of-truth records.

This avoids querying historical ChunkVersion and EmbeddingRecord tables directly during retrieval.

## Returned References

Each retrieved chunk includes IDs for:

- vector_index_entry_id
- source_document_id
- document_version_id
- section_version_id
- chunk_version_id
- embedding_record_id

These references prepare the system for grounded answer generation and citation traceability.

## Validation Rules

The retrieval request enforces:

- query must not be blank
- top_k must be at least 1
- top_k must not exceed MAX_RETRIEVAL_TOP_K
- provider must not be blank
- model_name must not be blank

## Current Limitations

The current API returns retrieved chunks only.

It does not yet:

- generate a final answer
- cite sources in natural language
- persist query traces
- evaluate retrieval quality
- apply tenant/workspace filters
- use a production embedding provider by default

## Future Work

Future slices should introduce:

- query tracing
- grounded answer generation
- citation formatting
- retrieval evaluation datasets
- provider configuration
- production pgvector indexes such as HNSW or IVFFlat