# Demo API Examples

## Purpose

This document provides API examples for manually demonstrating the Incremental RAG Indexing Platform.

The examples assume the API is running locally and fake providers are enabled by default.

Base URL:

    http://localhost:8000

If your local API uses a different port, adjust the examples.

## Provider Configuration

The retrieval provider and retrieval model are selected in request bodies using:

- provider
- model_name

The LLM provider is selected by runtime configuration:

    LLM_PROVIDER=fake

or:

    LLM_PROVIDER=openai

The answer request body should not include `llm_provider`, `llm_model_name`, `retrieval_provider`, or `retrieval_model_name`.

## Local Setup

Start Postgres and apply migrations:

    docker compose up -d postgres
    python -m alembic upgrade head

Validate the dataset:

    python scripts/preview_demo_dataset.py

Preview indexing without DB writes:

    python scripts/seed_demo_dataset.py --dry-run

Index the dataset:

    python scripts/seed_demo_dataset.py

Start the API:

    uvicorn app.main:create_app --factory --reload

Or use the Docker-based API startup flow if preferred.

## Health Check

Request:

    curl http://localhost:8000/health

Expected behavior:

- API responds successfully
- local environment is running

## Semantic Retrieval

Request:

    curl -X POST http://localhost:8000/api/v1/retrieval/search \
      -H "Content-Type: application/json" \
      -d '{
        "query": "Who owns Project Atlas?",
        "top_k": 5,
        "provider": "fake",
        "model_name": "fake-embedding-v1"
      }'

Expected behavior:

- response includes retrieval results
- response includes query_trace_id
- Project Atlas ownership chunk should appear in top_k

## Query Trace List

Request:

    curl http://localhost:8000/api/v1/retrieval/traces

Expected behavior:

- response includes recent query traces
- latest trace should correspond to the retrieval request

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
        "question": "Who owns Project Atlas?",
        "top_k": 5,
        "provider": "fake",
        "model_name": "fake-embedding-v1"
      }'

Expected behavior:

- response returns HTTP 200
- answer is persisted
- provider call is persisted
- usage summary is updated

With fake embeddings, answer quality depends on the highest-ranked retrieved chunk.

If the correct chunk appears in top_k but not first, the persisted answer may not be ideal. Use query traces and retrieval evaluation to inspect the ranking.

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
- response includes citations when available
- response allows answer auditability

## List LLM Provider Calls

Request:

    curl http://localhost:8000/api/v1/llm-provider-calls

Expected behavior:

- response includes provider call records
- latest call should match the grounded answer request
- provider/model/status should be inspectable
- failed provider calls should be visible when provider errors occur

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
- fake or OpenAI provider/model should appear after answer generation

## Create Retrieval Evaluation Case

The exact expected_chunk_version_ids must reference real chunk version IDs created during indexing.

Request shape:

    curl -X POST http://localhost:8000/api/v1/evaluation/cases \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Project Atlas ownership",
        "query": "Who owns Project Atlas?",
        "expected_chunk_version_ids": ["replace-with-indexed-chunk-version-id"],
        "tags": ["project-atlas", "ownership"]
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
2. Dry-run demo indexing.
3. Index demo dataset.
4. Run semantic retrieval.
5. Inspect query trace.
6. Generate grounded answer.
7. Inspect persisted answer.
8. Inspect provider call record.
9. Inspect usage summary.
10. Create or inspect evaluation cases.
11. Run retrieval evaluation.
12. Inspect evaluation results.

## Notes

The examples use fake retrieval providers by default.

Real LLM provider integration should be enabled only through explicit runtime configuration and should never be required for automated tests.

OpenAI rate-limit failures are valid observability data, but they are not a successful real-provider demo.