# Incremental RAG Indexing Platform

## Project Thesis

This is an AI infrastructure and Retrieval-Augmented Generation (RAG) indexing platform focused on incremental document processing, grounded answers, citation auditability, provider observability, usage and cost reporting, and retrieval evaluation.

It is not a chatbot. The emphasis is on versioning, retrieval correctness, operational traceability, and measurable retrieval quality.

## Why This Project Exists

Enterprise knowledge changes continuously. Naive RAG systems often re-index entire documents on every edit. That approach is wasteful, hard to audit, and expensive at scale.

This platform addresses engineering problems such as:

- detecting what changed in a document and reprocessing only affected sections and chunks
- preserving immutable version history for documents, sections, and chunks
- projecting a current vector index from durable source and embedding records
- measuring retrieval quality instead of relying on anecdotal answer inspection
- persisting LLM provider calls, including failures, for audit and cost analysis
- making estimated usage and cost visible by provider and model

## Core Capabilities

Implemented capabilities include:

- Incremental local Markdown document ingestion with checksum-driven change detection
- Document, section, and chunk versioning
- Embedding generation with cross-version reuse where input is unchanged
- Current vector index projection for semantic retrieval
- Semantic retrieval API with query traces
- Grounded answer generation with persisted answers and citations
- LLM provider boundary with fake provider as default
- Optional OpenAI provider adapter
- Provider call persistence for successful and failed attempts
- Provider call read API
- LLM usage and cost reporting
- Retrieval evaluation framework with demo cases and seeding command
- Deterministic demo dataset and manifest-driven indexing workflow
- Health and readiness endpoints

## Architecture Overview

High-level data and request flow:

```text
Source documents
  -> document versions
  -> section/chunk versions
  -> embeddings
  -> vector index entries
  -> retrieval
  -> query traces
  -> grounded answers
  -> citations / provider calls / usage reports
```

Architecture choices:

- modular monolith with API, application, domain, and infrastructure layers
- domain entities separated from SQLAlchemy persistence models
- repository contracts between application services and infrastructure
- LLM access through a provider boundary rather than direct SDK coupling in services
- `vector_index_entries` as the current retrieval projection, rebuildable from versions and embeddings
- retrieval evaluation as a persistent measurement layer for ranking quality

See [System Overview](docs/architecture/system-overview.md) for deeper architecture documentation.

## Tech Stack

- Python 3.12+
- FastAPI
- PostgreSQL with pgvector
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- pytest
- Docker and Docker Compose
- optional OpenAI provider adapter

## Local Setup

1. Clone the repository.
2. Create and activate a Python 3.12+ environment.
3. Install dependencies:

```bash
pip install -e ".[dev]"
```

4. Copy environment defaults and adjust locally:

```bash
cp .env.example .env
```

5. Start PostgreSQL:

```bash
docker compose up -d postgres
```

6. Apply migrations:

```bash
python -m alembic upgrade head
```

7. Start the API:

```bash
uvicorn app.main:create_app --factory --reload
```

Alternatively, run the API through Docker Compose:

```bash
docker compose up --build
```

API docs are available at `http://localhost:8000/docs` when the server is running.

## Environment Variables

Important variables from `.env.example`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SEED_DOCUMENTS_PATH` | Path to local seed Markdown documents |
| `LLM_PROVIDER` | LLM provider selection; default is `fake` |
| `OPENAI_API_KEY` | Optional; required only when `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | OpenAI model name when OpenAI is enabled |
| `OPENAI_TIMEOUT_SECONDS` | Provider request timeout |
| `OPENAI_MAX_OUTPUT_TOKENS` | Output token cap for OpenAI requests |
| `OPENAI_INPUT_PRICE_PER_1M_TOKENS_USD` | Estimated input pricing for cost reporting |
| `OPENAI_OUTPUT_PRICE_PER_1M_TOKENS_USD` | Estimated output pricing for cost reporting |

Never commit `.env` or API keys.

## Deterministic Demo

The reliable local demo uses fake providers and does not require external API keys.

```bash
python scripts/preview_demo_dataset.py
python scripts/seed_demo_dataset.py --dry-run
python scripts/seed_demo_dataset.py
```

With the API running:

1. Run semantic retrieval.
2. Generate a grounded answer with the default fake LLM provider.
3. Inspect persisted answers, provider calls, and usage summaries.
4. Seed and run retrieval evaluation:

```bash
python scripts/seed_demo_evaluation_cases.py --dry-run
python scripts/seed_demo_evaluation_cases.py
```

Detailed walkthroughs:

- [Final Demo Walkthrough](docs/demo/final-demo-walkthrough.md)
- [End-to-End Demo Guide](docs/demo/manual-flows/end-to-end-demo-guide.md)
- [Demo API Examples](docs/demo/manual-flows/api-examples.md)
- [Retrieval Evaluation Workflow](docs/demo/manual-flows/retrieval-evaluation-workflow.md)
- [Demo Checklist](docs/demo/manual-flows/demo-checklist.md)

## API Overview

Base prefix: `/api/v1`

| Area | Examples |
|---|---|
| Health / readiness | `GET /health`, `GET /readiness` |
| Ingestion | `POST /ingestion/local-seed-documents/discover`, `POST /ingestion/local-seed-documents/runs` |
| Retrieval | `POST /retrieval/search`, `GET /retrieval/traces`, `GET /retrieval/traces/{trace_id}` |
| Answers | `POST /answers`, `GET /answers`, `GET /answers/{answer_id}` |
| Provider calls | `GET /llm-provider-calls`, `GET /llm-provider-calls/{provider_call_id}` |
| Usage reporting | `GET /llm-usage/summary`, `GET /llm-usage/by-model` |
| Evaluation | `POST /evaluation/cases`, `POST /evaluation/runs`, `GET /evaluation/results` |

See [Demo API Examples](docs/demo/manual-flows/api-examples.md) for request and response examples.

## Testing

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app tests
```

Automated tests use fake providers by design and do not call OpenAI or other external LLM APIs.

## Provider Strategy

- `FakeEmbeddingProvider` and `FakeLLMProvider` are the defaults for local development and CI.
- OpenAI is supported as an optional provider behind the same boundary.
- External provider failures are persisted and auditable through provider call records.
- Real provider usage depends on local credentials, provider availability, quota, and rate limits.
- The local deterministic demo does not require external LLM calls.

Manual OpenAI validation is documented in [OpenAI Provider Setup](docs/providers/openai-provider-setup.md) and [OpenAI Manual Smoke Test](docs/providers/openai-manual-smoke-test.md).

## Retrieval Evaluation

Retrieval evaluation provides objective measurement of ranking quality over a known case set.

Metrics include:

- `hit_rate_at_k`
- `recall_at_k`
- `reciprocal_rank`

Fake embeddings are deterministic and suitable for local testing, but they do not approximate production semantic embedding quality. Evaluation makes ranking limitations visible and supports future comparisons across embedding providers, chunking strategies, reranking, and retrieval parameters.

See [Retrieval Evaluation Framework](docs/architecture/retrieval-evaluation-framework.md).

## Production Readiness

The platform is not deployed as a production service.

See the [Production Readiness Guide](docs/operations/production-readiness.md) for a clear breakdown of the platform's current production-minded capabilities, local/demo assumptions, and remaining requirements before real deployment.

## Known Limitations

- Fake embeddings are deterministic but not semantic-quality production embeddings.
- OpenAI is optional and depends on local credentials, provider availability, quota, and rate limits.
- Authentication and authorization are outside the current repository scope and would be required before exposing the platform as a public or multi-user service.
- Production deployment manifests, budget enforcement, and circuit breaker behavior are not included in this repository.
- Keyword and hybrid retrieval are not part of the current application surface.
- There is no public hosted demo.

## Roadmap

Potential next hardening and quality work:

- stronger embedding provider comparison
- reranking and hybrid retrieval
- budget guardrails
- provider fallback and circuit breaker behavior
- authentication and authorization if exposed as a public service
- scheduled retrieval evaluation
- deployment automation and operational dashboards

## Documentation

- [Project Status](docs/project-status.md)

Key documentation areas:

```text
docs/architecture/
docs/adr/
docs/demo/
docs/operations/
docs/providers/
```

Architecture documents explain how the system works. ADRs record technical decisions. Demo and provider docs cover manual workflows and optional real-provider validation.
