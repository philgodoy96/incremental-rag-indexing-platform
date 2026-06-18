# Demo API Examples

## Purpose

This document provides API examples for manually demonstrating the Incremental RAG Indexing Platform.

The examples assume the API is running locally and fake providers are enabled.

Base URL:

    http://localhost:8000

If your local API uses a different port, adjust the examples.

## Health Check

Request:

    curl http://localhost:8000/health

Expected behavior:

- API responds successfully
- local environment is running

## Preview Demo Dataset

The dataset preview runs as a local script:

    python scripts/preview_demo_dataset.py

Expected behavior:

- dataset name is printed
- dataset version is printed
- four demo documents are listed
- each document has a checksum

## Semantic Retrieval

Request:

    curl -X POST http://localhost:8000/api/v1/retrieval/search \
      -H "Content-Type: application/json" \
      -d '{
        "query": "What is Project Atlas?",
        "top_k": 5,
        "provider": "fake",
        "model_name": "fake-embedding-v1"
      }'

Expected behavior:

- response includes retrieval results
- top results should reference Project Atlas content
- a query trace is created or can be inspected afterward

## Query Trace List

Request:

    curl http://localhost:8000/api/v1/retrieval/traces

Expected behavior:

- response includes recent query traces
- the latest trace should correspond to the retrieval request

## Query Trace Detail

Request:

    curl http://localhost:8000/api/v1/retrieval/traces/{query_trace_id}

Expected behavior:

- response includes query text
- response includes retrieval hits
- response includes provider/model metadata

## Generate Grounded Answer

Request:

    curl -X POST http://localhost:8000/api/v1/answers \
      -H "Content-Type: application/json" \
      -d '{
        "query": "Who owns Project Atlas?",
        "top_k": 5,
        "retrieval_provider": "fake",
        "retrieval_model_name": "fake-embedding-v1",
        "llm_provider": "fake",
        "llm_model_name": "fake-llm-v1"
      }'

Expected behavior:

- response includes an answer
- response includes citations
- answer is persisted
- provider call is persisted

## List Answers

Request:

    curl http://localhost:8000/api/v1/answers

Expected behavior:

- response includes persisted answers
- latest answer should match the previous grounded answer request

## Answer Detail

Request:

    curl http://localhost:8000/api/v1/answers/{answer_id}

Expected behavior:

- response includes answer content
- response includes citations
- response allows answer auditability

## List LLM Provider Calls

Request:

    curl http://localhost:8000/api/v1/llm-provider-calls

Expected behavior:

- response includes provider call records
- latest call should match the grounded answer request
- provider/model/status should be inspectable

## LLM Provider Call Detail

Request:

    curl http://localhost:8000/api/v1/llm-provider-calls/{provider_call_id}

Expected behavior:

- response includes provider name
- response includes model name
- response includes status
- response includes usage metadata when available
- response includes error details for failed calls

## LLM Usage Summary

Request:

    curl http://localhost:8000/api/v1/llm-usage/summary

Expected behavior:

- response includes call_count
- response includes succeeded_count
- response includes failed_count
- response includes token totals when available
- response includes estimated_cost_usd

## LLM Usage By Model

Request:

    curl http://localhost:8000/api/v1/llm-usage/by-model

Expected behavior:

- response groups calls by provider and model
- fake provider/model should appear after answer generation

## Create Retrieval Evaluation Case

The exact expected_chunk_version_ids must reference real chunk version IDs created during indexing.

Request shape:

    curl -X POST http://localhost:8000/api/v1/evaluation/cases \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Project Atlas overview",
        "query": "What is Project Atlas?",
        "expected_chunk_version_ids": ["replace-with-indexed-chunk-version-id"],
        "tags": ["project-atlas", "overview"]
      }'

Expected behavior:

- response creates an evaluation case
- returned ID can be used in evaluation runs

## List Retrieval Evaluation Cases

Request:

    curl http://localhost:8000/api/v1/evaluation/cases

Expected behavior:

- response includes evaluation cases
- demo cases can be inspected

## Run Retrieval Evaluation

Request:

    curl -X POST http://localhost:8000/api/v1/evaluation/runs \
      -H "Content-Type: application/json" \
      -d '{
        "evaluation_case_ids": ["replace-with-evaluation-case-id"],
        "top_k": 5,
        "provider": "fake",
        "model_name": "fake-embedding-v1"
      }'

Expected behavior:

- response includes per-case results
- response includes summary metrics
- results are persisted

## List Retrieval Evaluation Results

Request:

    curl http://localhost:8000/api/v1/evaluation/results

Expected behavior:

- response includes persisted evaluation results
- status, recall_at_k, and reciprocal_rank are inspectable

## Recommended Demo Order

Use this sequence when presenting the project:

1. Preview demo dataset.
2. Load or index demo documents using the existing ingestion flow.
3. Run semantic retrieval.
4. Inspect query trace.
5. Generate grounded answer.
6. Inspect persisted answer.
7. Inspect provider call record.
8. Inspect usage summary.
9. Create or inspect evaluation cases.
10. Run retrieval evaluation.
11. Inspect evaluation results.

## Notes

The examples use fake providers by default.

Real provider integration should be enabled only through explicit configuration and should never be required for automated tests.