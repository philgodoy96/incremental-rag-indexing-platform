# Demo Checklist

Use this checklist before presenting the Incremental RAG Indexing Platform.

## Environment

- [ ] Postgres is running.
- [ ] Migrations are applied.
- [ ] API starts successfully.
- [ ] `.env` is ignored by Git.
- [ ] `LLM_PROVIDER=fake` is used for default local demo.
- [ ] No real API keys are committed.

## Dataset Validation

- [ ] `python scripts/preview_demo_dataset.py` runs successfully.
- [ ] Dataset name is shown.
- [ ] Dataset version is shown.
- [ ] Four demo documents are listed.
- [ ] Checksums are shown for each document.

## Dry Run

- [ ] `python scripts/seed_demo_dataset.py --dry-run` runs successfully.
- [ ] Manifest is loaded.
- [ ] Documents are discovered.
- [ ] No database writes are performed.

## Demo Indexing

- [ ] `python scripts/seed_demo_dataset.py` runs successfully.
- [ ] Demo documents are processed through the real ingestion pipeline.
- [ ] Document versions are created or unchanged documents are skipped.
- [ ] Chunks are available.
- [ ] Embeddings are available.
- [ ] Vector index entries are available.
- [ ] Rerun is safe for unchanged content.

## Retrieval

- [ ] `POST /api/v1/retrieval/search` returns non-empty results.
- [ ] Query trace ID is returned.
- [ ] Project Atlas ownership chunk appears in top_k for ownership query.
- [ ] Retrieval ranking is inspected rather than assumed perfect.

## Query Trace

- [ ] `GET /api/v1/retrieval/traces` returns traces.
- [ ] Latest trace can be read.
- [ ] Trace includes query text.
- [ ] Trace includes hit records.
- [ ] Trace includes provider/model metadata.

## Grounded Answer

- [ ] `POST /api/v1/answers` returns HTTP 200 with valid payload.
- [ ] Answer is persisted.
- [ ] Answer includes status.
- [ ] Answer includes query_trace_id.
- [ ] Citations exist when context is available.

## Provider Calls

- [ ] `GET /api/v1/llm-provider-calls` returns provider call records.
- [ ] Successful fake provider call is visible.
- [ ] Failed provider calls are visible when failures were simulated.
- [ ] Failed OpenAI calls are recorded if provider rate limits occur.

## Usage Reporting

- [ ] `GET /api/v1/llm-usage/summary` returns aggregate usage.
- [ ] call_count is updated.
- [ ] succeeded_count is updated.
- [ ] failed_count is updated when failures occur.
- [ ] token totals are recorded when available.
- [ ] estimated cost is recorded when available.


## Retrieval Evaluation Case Seeding

- [ ] `python scripts/seed_demo_evaluation_cases.py --dry-run` runs successfully.
- [ ] `python scripts/seed_demo_evaluation_cases.py` creates demo evaluation cases.
- [ ] Rerun skips identical cases.
- [ ] `GET /api/v1/evaluation/cases` lists the five demo cases.
- [ ] Expected chunk version IDs are populated.
## Evaluation

- [ ] Evaluation cases can be created or inspected.
- [ ] Evaluation run can be executed.
- [ ] Results are persisted.
- [ ] hit_rate_at_k is visible.
- [ ] recall_at_k is visible.
- [ ] reciprocal rank is visible.

## Known Limitations To Explain

- [ ] Fake embeddings are deterministic but not high-quality semantic embeddings.
- [ ] Correct chunks may appear in top_k without ranking first.
- [ ] Fake LLM answers may summarize the top-ranked chunk.
- [ ] Retrieval evaluation exists to make ranking quality measurable.
- [ ] OpenAI smoke tests may fail due to provider rate limits.
- [ ] A failed OpenAI provider call is not a successful real-provider demo.