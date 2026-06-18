# Project Status

## Status

The repository scope is **complete for the current project goals**.

This platform is a working local system with automated tests, deterministic demo workflows, and documented architecture. It is not production-deployed and is not fully production-ready.

## Project Scope

This repository is an AI infrastructure and Retrieval-Augmented Generation (RAG) indexing platform focused on:

- incremental indexing
- grounded answers
- citations
- provider observability
- usage and cost reporting
- retrieval evaluation

It is not a chatbot. The emphasis is on versioning, retrieval correctness, operational traceability, and measurable retrieval quality.

## Implemented Capabilities

### Ingestion and indexing

- manifest-driven demo dataset
- source documents
- document versions
- section versions
- chunk versions
- embeddings
- active vector index entries
- checksum-driven unchanged document handling where implemented

### Retrieval

- semantic retrieval API
- query trace persistence
- current vector index projection

### Answering

- grounded answer API
- persisted answers
- citations
- insufficient-context handling when applicable

### Provider observability

- LLM provider boundary
- fake provider default
- optional OpenAI provider adapter
- provider call persistence
- failed external provider call persistence as a general capability
- provider call read API

### Usage and cost reporting

- token usage metadata
- estimated cost reporting
- usage summary
- by-model usage reporting

### Evaluation

- retrieval evaluation framework
- demo evaluation case definitions
- demo evaluation seeding command
- evaluation run API
- persisted evaluation results
- metrics such as `hit_rate_at_k`, `recall_at_k`, `reciprocal_rank`

### Demo

- deterministic demo documents
- demo dataset preview
- demo dataset indexing command
- final demo walkthrough

## Local Demo Path

The reliable local demo uses fake providers and does not require external API keys:

1. preview demo dataset
2. seed/index demo dataset
3. run retrieval
4. run answer with fake provider
5. inspect provider calls and usage
6. seed evaluation cases
7. run evaluation

See [Final Demo Walkthrough](demo/final-demo-walkthrough.md) for step-by-step instructions.

## Provider Strategy

- fake providers are the default for local development and CI
- OpenAI is optional behind the same provider boundary
- real provider usage depends on local credentials, provider availability, quota, and rate limits
- the local demo does not require OpenAI

## Known Boundaries

These are intentional project boundaries for the current repository scope:

- not production-deployed
- fake embeddings are deterministic but not production-quality semantic embeddings
- authentication and authorization are out of scope for this repository, but required before public or multi-user deployment
- no production deployment manifests
- no enforced budget guardrails or circuit breaker unless implemented
- no public hosted demo
- no automatic provider fallback unless implemented

## Recommended Next Hardening

- production auth/RBAC if exposed publicly
- budget guardrails
- rate limiting
- retry/backoff and circuit breaker policy
- provider fallback strategy
- stronger embedding provider comparison
- reranking
- scheduled retrieval evaluation
- deployment and observability dashboards

## Validation Commands

Automated checks:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app tests
```

Core demo commands:

```bash
python scripts/preview_demo_dataset.py
python scripts/seed_demo_dataset.py --dry-run
python scripts/seed_demo_dataset.py
python scripts/seed_demo_evaluation_cases.py --dry-run
python scripts/seed_demo_evaluation_cases.py
```
