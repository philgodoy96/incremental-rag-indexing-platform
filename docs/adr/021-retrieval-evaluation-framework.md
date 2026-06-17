# ADR-021: Add Retrieval Evaluation Framework

## Status

Accepted

## Context

The platform supports incremental indexing, semantic retrieval, query tracing, grounded answers, answer persistence, LLM provider observability, and usage reporting.

However, it did not yet have a way to measure retrieval quality over time.

Without retrieval evaluation, changes to chunking, embeddings, ranking, filtering, indexing, or provider configuration can silently degrade the platform.

Production RAG systems need repeatable retrieval quality checks.

## Decision

The system will introduce a Retrieval Evaluation Framework.

The framework includes:

- RetrievalEvaluationCase
- RetrievalEvaluationCaseResult
- RetrievalEvaluationRunSummary
- repositories and persistence
- evaluation runner
- APIs for cases, results, and run execution

Evaluation cases define:

- query
- expected_chunk_version_ids
- optional tags

The runner executes semantic retrieval for each case and compares retrieved_chunk_version_ids against expected_chunk_version_ids.

The first version will calculate:

- hit_count
- recall_at_k
- reciprocal_rank
- hit_rate_at_k
- mean_recall_at_k
- mean_reciprocal_rank

## Consequences

### Positive

- Retrieval quality can now be measured.
- Regressions can be detected manually through repeated evaluation runs.
- Evaluation cases create a reusable benchmark dataset.
- Results are persisted and inspectable through APIs.
- The project now better represents an AI infrastructure platform instead of a simple chatbot.
- Future CI and scheduled evaluation workflows can build on this foundation.

### Negative

- The framework adds more domain and persistence complexity.
- Evaluation run identity is not persisted yet.
- Metrics are still basic.
- Expected chunks must be curated manually.
- No baseline comparison exists yet.
- No automated regression threshold exists yet.

## Alternatives Considered

### Rely Only on Manual Testing

Rejected because manual query testing is not repeatable or measurable.

### Rely Only on Query Trace Inspection

Rejected because query traces explain individual searches but do not measure quality against expected results.

### Add Full Evaluation Suite Immediately

Deferred because a minimal but extensible evaluation framework is better for incremental delivery.

Additional metrics and persisted evaluation runs can be added later.

## Follow-Up

Future work should add:

- RetrievalEvaluationRun persistence
- dataset naming/versioning
- baseline comparison
- scheduled evaluations
- precision@k
- nDCG
- per-tag metrics
- CI regression checks
- historical reports