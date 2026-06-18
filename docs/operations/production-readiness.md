# Production Readiness Guide

## 1. Purpose

This guide provides a clear breakdown of the platform's current production-minded capabilities, local and demo assumptions, and remaining requirements before deployment beyond controlled environments.

The platform is an AI infrastructure and RAG indexing system with a deterministic local demo workflow. It implements incremental indexing, retrieval auditability, grounded answers with citations, provider observability, and retrieval evaluation. It is not deployed as a production service.

Use this guide to identify appropriate defaults for local development and CI, capabilities that support operational inspection, and deployment hardening considerations before wider exposure.

## 2. Current Production-Minded Capabilities

The following areas reflect backend design choices that support reliability, auditability, and operational inspection.

### Incremental indexing and checksum-driven change detection

The ingestion pipeline detects source, document, section, and chunk changes using checksums. Unchanged content can be skipped instead of being fully reprocessed. See [Incremental Indexing Strategy](../architecture/incremental-indexing-strategy.md).

### Document and chunk versioning

The system persists immutable version chains:

- source documents
- document versions
- section versions
- chunk versions

This supports auditability, reproducibility, and targeted re-indexing when only part of a document changes.

### Vector index projection

Embeddings are stored as durable records. Active vector index entries represent the current retrieval projection and can be rebuilt from source versions and embedding records. See [Vector Index Projection](../architecture/vector-index-projection.md).

### Grounded answer persistence

Grounded answers are persisted with links to the query trace and retrieved evidence. Answers can be listed and inspected after generation. See [Answer Persistence](../architecture/answer-persistence.md) and [Grounded Answer Flow](../architecture/grounded-answer-flow.md).

### Citation auditability

Each grounded answer can include persisted citations that point back to retrieved chunk evidence. This supports post-hoc inspection of what evidence supported a response.

### Provider call persistence

Successful LLM provider calls are persisted with provider identity, model name, latency, token usage when available, and estimated cost when usage is available. Calls can be inspected by answer or listed directly. See [LLM Provider Call Read API](../architecture/llm-provider-call-read-api.md).

### Failed provider call auditability

When answer generation fails after retrieval succeeds, the failed provider attempt is still persisted as a provider call record with error details. Failed calls are inspectable through the same read API. See [Failed LLM Provider Call Persistence](../architecture/failed-llm-provider-call-persistence.md).

### Usage and cost reporting

Aggregated LLM usage can be queried by time range, provider, and model. Reporting includes call counts, success and failure counts, token totals, estimated cost, and average latency. See [LLM Usage Reporting API](../architecture/llm-usage-reporting-api.md).

### Retrieval evaluation

The platform includes persistent evaluation cases, per-case results, run summaries, and APIs to execute evaluations. Metrics include `hit_rate_at_k`, `recall_at_k`, and `reciprocal_rank`. See [Retrieval Evaluation Framework](../architecture/retrieval-evaluation-framework.md).

### Deterministic demo workflow

A manifest-driven demo dataset, indexing command, evaluation case seeding command, and manual demo documentation provide a repeatable local workflow for validating end-to-end behavior without external providers. See [End-to-End Demo Guide](../demo/manual-flows/end-to-end-demo-guide.md).

### Health and readiness separation

The API exposes separate health and readiness endpoints. Health indicates process liveness. Readiness checks PostgreSQL connectivity and pgvector availability. See [ADR-003](../adr/003-separate-health-and-readiness-checks.md).

## 3. Local and Demo Defaults

### Fake providers are the default

Both the embedding provider and the LLM provider default to fake implementations:

- `FakeEmbeddingProvider` is wired into ingestion and semantic retrieval
- `LLM_PROVIDER=fake` is the default application setting

This keeps local development and automated tests deterministic, fast, and free of external API dependencies.

### Fake providers support tests and CI

Automated tests use fake providers by design. The test suite does not call OpenAI or other external LLM APIs.

### OpenAI is optional

OpenAI integration exists as an optional adapter behind the LLM provider boundary. It is enabled only through explicit environment configuration and a valid API key. See [OpenAI Provider Setup](../providers/openai-provider-setup.md).

### Local demo works without external API keys

The default demo workflow runs indexing, retrieval, grounded answers, provider call inspection, usage reporting, and retrieval evaluation using fake providers. No external API keys are required for that path.

## 4. Provider Strategy

### LLM provider boundary

Answer generation goes through a provider interface. Application services depend on the boundary, not on a specific vendor SDK. Provider selection is configuration-driven.

### Fake provider

The fake LLM provider is the default. It produces deterministic behavior suitable for development, demos, and CI. It is not a substitute for production answer quality evaluation.

### OpenAI provider

An OpenAI adapter is available for controlled manual validation. Real calls may fail because of rate limits, timeouts, invalid credentials, model availability, or provider outages. The repository does not require successful real-provider answer generation for local or CI validation.

Manual validation steps are documented in [OpenAI Manual Smoke Test](../providers/openai-manual-smoke-test.md). Record outcomes in [Real Provider Observations Template](../demo/real-provider-observations-template.md) as part of controlled validation.

### Failure capture

Provider failures during answer generation are mapped to structured errors and persisted as failed provider call records when applicable. This includes rate limit and timeout failures from external provider adapters.

### Rate limits

External providers can enforce rate limits. The platform records those failures but does not automatically retry or switch providers today.

### No automatic fallback

There is no automatic provider fallback or circuit breaker in the current implementation. A failed real-provider call remains failed unless the caller retries or configuration is changed.

### Future provider resilience options

Planned extensions include retry with backoff, provider fallback, circuit breaker behavior, and fallback model metadata. These are not implemented in the current codebase.

## 5. Data and Indexing Readiness

### Source documents

`SourceDocument` records represent discovered source files and metadata for the local seed source system.

### Version chain

Indexing creates and maintains:

- document versions for full-document snapshots
- section versions for structure-aware sections
- chunk versions for deterministic retrieval units

### Embeddings

New or changed chunks can receive embedding records. The platform supports embedding reuse across versions when embedding input is unchanged.

### Vector index entries

Active vector index entries are the current retrieval projection used by semantic search. They should reflect the latest successful indexing outcome for each chunk.

### Checksum-driven and idempotent ingestion behavior

Ingestion compares checksums to detect unchanged documents and avoid unnecessary version creation. Demo dataset seeding supports `--dry-run` preview. Re-running unchanged demo indexing or evaluation seeding should skip duplicate work where implemented.

### Demo indexing command

Index the deterministic demo dataset:

```bash
docker compose up -d postgres
python -m alembic upgrade head
python scripts/seed_demo_dataset.py
```

Preview without writes:

```bash
python scripts/seed_demo_dataset.py --dry-run
```

## 6. Retrieval and Evaluation Readiness

### Retrieval API

Semantic retrieval is available at `POST /api/v1/retrieval/search`. Each search can create a query trace that records the query, retrieval parameters, and ranked hits.

### Query traces

Query traces can be listed and inspected by ID. They support debugging retrieval behavior independently from answer generation.

### Demo evaluation cases

Demo evaluation cases can be seeded after the demo dataset is indexed:

```bash
python scripts/seed_demo_evaluation_cases.py --dry-run
python scripts/seed_demo_evaluation_cases.py
```

See [Retrieval Evaluation Workflow](../demo/manual-flows/retrieval-evaluation-workflow.md).

### Metrics

Per-case metrics include:

- `recall_at_k`: fraction of expected chunks found in the top-k results
- `reciprocal_rank`: rank-based score for the first expected hit

Run-level summary metrics include:

- `hit_rate_at_k`: fraction of cases with at least one expected chunk in top-k
- `mean_recall_at_k`
- `mean_reciprocal_rank`

### Interpreting low fake-provider metrics

Fake embeddings are deterministic and suitable for local testing, but they do not approximate production semantic embedding quality. A local evaluation run may return expected chunks in top-k without ranking them first. That indicates retrieval ranking behavior, not an ingestion failure.

Lower fake-provider metrics show that the evaluation framework detects ranking weakness before introducing a production embedding model or reranker. The relevant measure is retrieval quality observability, not fake-embedding ranking performance.

## 7. Cost Observability Readiness

### Provider calls

Individual LLM provider calls are persisted for both successful and failed attempts where applicable.

### Token usage metadata

Successful calls can store prompt, completion, and total token counts when the provider returns usage metadata.

### Estimated cost

Estimated cost in USD can be stored when token usage and configured per-model pricing are available.

### Usage summary

`GET /api/v1/llm-usage/summary` aggregates usage over a time range with optional provider and model filters.

### By-model reporting

`GET /api/v1/llm-usage/by-model` returns grouped usage and cost metrics per provider and model.

### Reporting constraints

Cost and token reporting depend on provider behavior:

- fake provider calls use deterministic test metadata
- failed calls persist zero token usage and zero estimated cost
- if a real provider does not return usage metadata, token and cost fields may be incomplete
- configured pricing is an estimate and may drift from actual provider billing

## 8. Deployment Requirements Outside Current Scope

The following capabilities are outside the current repository scope. They are required before exposing the platform as a public or multi-user service or operating it at production scale.

### Authentication and authorization

Authentication and authorization are intentionally outside the current project scope. They would be required before exposing the platform as a public or multi-user service.

### Multi-tenant security

There is no full multi-tenant isolation layer, tenant-scoped authorization, or per-tenant data partitioning unless added externally at deployment time.

### Budget guardrails

There are no enforced spending limits, per-tenant budgets, or automatic shutdown on cost thresholds.

### Production deployment manifests

There is no production-grade Kubernetes, Terraform, or cloud deployment packaging in this repository. Docker Compose supports local development only.

### Background worker scaling

Ingestion and indexing run synchronously in the current application flow. There is no separate worker fleet, queue-backed job system, or horizontal scaling model for indexing workloads.

### Full observability stack

Structured logging exists, but there is no bundled Prometheus, Grafana, OpenTelemetry, or alerting stack. Health and readiness endpoints are available; a full observability stack would be added at deployment time.

### Vector database tuning benchmarks

pgvector is used for semantic search, but the repository does not include production benchmarking for index type selection, recall/latency tradeoffs, or large-corpus tuning.

### Automated real-provider tests

Automated tests deliberately avoid real external provider calls. Real-provider behavior must be validated manually under controlled conditions.

### Keyword and hybrid retrieval

Semantic retrieval is implemented. Keyword and hybrid retrieval are described in broader architecture planning but are not part of the current application surface.

## 9. Failure Modes to Monitor

When operating or hardening a deployment, monitor for the following:

| Failure mode | Why it matters |
|---|---|
| Provider rate limits | Answer generation fails even when retrieval succeeds; failures should appear in provider call records |
| Provider timeouts | Slow or hanging provider calls affect latency and may produce failed provider records |
| Empty retrieval | Grounded answers may have little or no evidence; query traces help distinguish retrieval failure from generation failure |
| Stale vector index entries | Retrieval may return outdated chunks if projection updates lag behind version changes |
| Duplicate ingestion attempts | Repeated runs should be safe, but unexpected duplicate versions or jobs may indicate caller or orchestration issues |
| Missing expected chunks | Section/chunk extraction or indexing gaps reduce recall and appear in evaluation metrics |
| Weak retrieval ranking | Expected chunks may appear below rank 1 or outside top-k; evaluation metrics surface this |
| Cost spikes | Usage summaries and per-model reporting should be reviewed when enabling real providers |
| Schema or migration drift | Database schema must match application code; readiness checks do not replace migration discipline |

## 10. Pre-Deployment Checklist

Use this checklist before exposing the platform beyond a private development environment.

- [ ] Configure secrets safely. Store API keys and database credentials in a secret manager or secure environment injection. Never commit secrets to the repository.
- [ ] Configure provider. Choose `fake` for deterministic environments or `openai` only when real-provider validation is intentional.
- [ ] Configure database. Provide a production-grade PostgreSQL instance with pgvector enabled.
- [ ] Run migrations. Apply Alembic migrations before serving traffic.
- [ ] Seed or connect sources. Load initial documents through the supported ingestion path or connect an approved source integration.
- [ ] Run retrieval evaluation. Seed or create evaluation cases and execute an evaluation run to establish a baseline.
- [ ] Configure logging and metrics. Ensure application logs and dependency health are collected centrally.
- [ ] Configure rate limits. Apply ingress and provider-side throttling appropriate to expected load.
- [ ] Configure budgets. Define external spending alerts or limits if real providers are enabled.
- [ ] Configure backups. Back up PostgreSQL and verify restore procedures.
- [ ] Configure incident response. Define ownership for provider outages, retrieval regressions, and database failures.

## 11. Recommended Deployment Hardening

The following sequence supports teams preparing the platform for wider deployment.

1. Add authentication and authorization at the deployment boundary.
2. Add budget limits and cost alerts for real providers.
3. Add API rate limiting and abuse protection.
4. Add retry and backoff policy for transient provider failures.
5. Add provider fallback and circuit breaker behavior.
6. Move long-running ingestion to background jobs or workers.
7. Add observability dashboards and alerting.
8. Add production deployment automation and environment separation.
9. Introduce stronger embeddings, reranking, or hybrid retrieval where retrieval quality requires it.
10. Schedule recurring retrieval evaluation against a stable case set.

## Related Documentation

- [Final Demo Walkthrough](../demo/final-demo-walkthrough.md)
- [System Overview](../architecture/system-overview.md)
- [OpenAI Provider Setup](../providers/openai-provider-setup.md)
- [Fake vs Real Provider Comparison](../demo/fake-vs-real-provider-comparison.md)
- [End-to-End Demo Guide](../demo/manual-flows/end-to-end-demo-guide.md)
- [Retrieval Evaluation Workflow](../demo/manual-flows/retrieval-evaluation-workflow.md)
- [Demo Checklist](../demo/manual-flows/demo-checklist.md)
