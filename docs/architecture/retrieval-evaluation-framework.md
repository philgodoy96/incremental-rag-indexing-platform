# Retrieval Evaluation Framework

## Purpose

The Retrieval Evaluation Framework measures retrieval quality over time.

A RAG platform is only as reliable as its retrieval layer.

The system may generate grounded answers, persist citations, and expose query traces, but without evaluation there is no objective way to know whether retrieval quality improves or degrades after changes to:

- chunking strategy
- embedding model
- vector index projection
- ranking logic
- filters
- indexing behavior
- query transformation
- provider configuration

This framework introduces persistent evaluation cases, evaluation results, aggregate metrics, a runner, and APIs to execute and inspect retrieval evaluations.

## Why This Matters

In production RAG systems, retrieval regressions can happen silently.

Examples:

- a chunking change removes useful context
- a new embedding model changes nearest-neighbor behavior
- metadata filtering becomes too restrictive
- indexing misses a changed section
- ranking returns the right document but the wrong chunk
- retrieval works for common questions but fails for edge cases

The evaluation framework creates a repeatable way to test retrieval quality against known expected chunks.

## Core Concepts

### RetrievalEvaluationCase

A RetrievalEvaluationCase defines one evaluation input.

It includes:

- id
- name
- query
- expected_chunk_version_ids
- tags
- created_at

The key field is expected_chunk_version_ids.

These are the chunks that should be retrieved for the query.

### RetrievalEvaluationCaseResult

A RetrievalEvaluationCaseResult stores the result of running retrieval for one evaluation case.

It includes:

- evaluation_case_id
- query
- expected_chunk_version_ids
- retrieved_chunk_version_ids
- status
- top_k
- hit_count
- recall_at_k
- reciprocal_rank
- error_message
- created_at

### RetrievalEvaluationRunSummary

RetrievalEvaluationRunSummary aggregates results from one run.

It includes:

- case_count
- succeeded_count
- failed_count
- hit_count
- total_expected_count
- hit_rate_at_k
- mean_recall_at_k
- mean_reciprocal_rank

## Metrics

### hit_count

The number of expected chunks that appeared in the retrieved results.

### recall_at_k

The fraction of expected chunks found in the top-k retrieved results.

Example:

    expected = [A, B]
    retrieved = [C, B, D]
    hit_count = 1
    recall_at_k = 0.5

### reciprocal_rank

The inverse rank of the first relevant retrieved chunk.

Example:

    expected = [B]
    retrieved = [A, B, C]
    first hit is rank 2
    reciprocal_rank = 1 / 2 = 0.5

### hit_rate_at_k

The fraction of evaluation cases where at least one expected chunk was retrieved.

### mean_recall_at_k

The average recall_at_k across all case results.

### mean_reciprocal_rank

The average reciprocal_rank across all case results.

## API Endpoints

### Create evaluation case

POST /api/v1/evaluation/cases

Example request:

    {
      "name": "Project Atlas status",
      "query": "What is Project Atlas status?",
      "expected_chunk_version_ids": ["uuid"],
      "tags": ["status", "project-atlas"]
    }

### List evaluation cases

GET /api/v1/evaluation/cases

Supported query parameters:

- limit
- offset
- tag

### Get evaluation case

GET /api/v1/evaluation/cases/{evaluation_case_id}

### List results for case

GET /api/v1/evaluation/cases/{evaluation_case_id}/results

### List evaluation results

GET /api/v1/evaluation/results

Supported query parameters:

- limit
- offset
- status

### Get evaluation result

GET /api/v1/evaluation/results/{evaluation_case_result_id}

### Run evaluation

POST /api/v1/evaluation/runs

Example request:

    {
      "evaluation_case_ids": ["uuid"],
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Example response:

    {
      "results": [
        {
          "id": "uuid",
          "evaluation_case_id": "uuid",
          "query": "What is Project Atlas status?",
          "expected_chunk_version_ids": ["uuid"],
          "retrieved_chunk_version_ids": ["uuid"],
          "status": "succeeded",
          "top_k": 5,
          "hit_count": 1,
          "recall_at_k": 1.0,
          "reciprocal_rank": 1.0,
          "error_message": null,
          "created_at": "2026-06-17T00:00:00Z"
        }
      ],
      "summary": {
        "case_count": 1,
        "succeeded_count": 1,
        "failed_count": 0,
        "hit_count": 1,
        "total_expected_count": 1,
        "hit_rate_at_k": 1.0,
        "mean_recall_at_k": 1.0,
        "mean_reciprocal_rank": 1.0
      }
    }

## Runner Flow

The evaluation runner performs the following steps:

1. Receives evaluation cases.
2. Runs semantic retrieval for each case query.
3. Extracts retrieved_chunk_version_ids.
4. Compares retrieved chunks with expected chunks.
5. Produces one RetrievalEvaluationCaseResult per case.
6. Persists all results.
7. Returns aggregate summary metrics.

## Failure Handling

If retrieval fails for one case, the runner creates a failed case result instead of failing the entire run.

A failed result has:

- status = failed
- hit_count = 0
- recall_at_k = 0.0
- reciprocal_rank = 0.0
- error_message populated

This allows evaluation runs to complete even when individual cases fail.

## Why Evaluation Is Separate From Query Trace

Query traces explain what happened during a specific retrieval request.

Evaluation measures whether retrieval produced expected results.

Both are necessary:

- QueryTrace = debugging one retrieval execution
- RetrievalEvaluation = measuring retrieval quality over a dataset

## Current Limitations

The current implementation does not yet support:

- persisted evaluation run entity with durable run IDs separate from case results
- named evaluation datasets
- scheduled evaluation jobs
- baseline comparison
- regression thresholds
- CI integration
- precision@k
- nDCG
- per-tag aggregate metrics
- historical charts
- workspace/tenant scoping

Evaluation cases, per-case results, run summaries, and evaluation APIs are implemented.

## Future Work

Future hardening may include:

- durable RetrievalEvaluationRun entity
- dataset management
- baseline comparison
- scheduled evaluation jobs
- regression detection
- precision@k and nDCG
- per-tag metrics
- CI checks for retrieval quality
- deployment-time dashboard endpoints
- evaluation reports over time