# Final Demo Walkthrough

## Purpose

This is the shortest reliable path to validate the Incremental RAG Indexing Platform locally.

It uses fake providers by default and does not require external API keys.

## What This Demo Proves

- deterministic dataset validation
- ingestion and indexing through the real pipeline
- active vector index entries
- semantic retrieval
- query trace creation
- grounded answer generation with the fake LLM provider
- persisted answers and citations
- provider call auditability
- usage reporting
- retrieval evaluation metrics

## Prerequisites

- Python 3.12+ environment with project dependencies installed (`pip install -e ".[dev]"`)
- PostgreSQL running locally
- Alembic migrations applied
- `.env` configured from `.env.example`
- `LLM_PROVIDER=fake` for the default demo path

OpenAI is not required for this walkthrough.

## Step 1: Start Dependencies

```bash
docker compose up -d postgres
python -m alembic upgrade head
```

Optional readiness check:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/readiness"
```

Run this after the API is started in Step 4.

## Step 2: Validate Deterministic Dataset

```bash
python scripts/preview_demo_dataset.py
```

Expected:

- manifest loads successfully
- four demo documents are listed
- each document shows a content checksum

## Step 3: Seed and Index Demo Dataset

Preview without database writes:

```bash
python scripts/seed_demo_dataset.py --dry-run
```

Index the dataset:

```bash
python scripts/seed_demo_dataset.py
```

Expected:

- source documents, document versions, section versions, chunk versions, embeddings, and active vector index entries are created
- rerun skips unchanged documents when checksums match

## Step 4: Start API

```bash
uvicorn app.main:create_app --factory --reload
```

Alternatively:

```bash
docker compose up --build
```

Confirm the API is up:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health"
```

Base URL for the steps below: `http://localhost:8000`

## Step 5: Run Retrieval

```powershell
$RetrievalPayload = @{
    query = "Who owns Project Atlas?"
    top_k = 5
    provider = "fake"
    model_name = "fake-embedding-v1"
} | ConvertTo-Json

$RetrievalResponse = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/retrieval/search" `
    -ContentType "application/json" `
    -Body $RetrievalPayload

$RetrievalResponse | ConvertTo-Json -Depth 20
```

Expected:

- `results` is not empty
- `query_trace_id` is returned
- a Project Atlas ownership chunk appears somewhere in `top_k`

Fake embeddings are deterministic but may not rank the best chunk first. That is expected and is one reason retrieval evaluation exists.

Optional trace inspection:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/retrieval/traces" |
    ConvertTo-Json -Depth 20
```

## Step 6: Generate Grounded Answer

Ensure `LLM_PROVIDER=fake` in `.env` before this step.

```powershell
$AnswerPayload = @{
    question = "Who owns Project Atlas?"
    top_k = 5
    provider = "fake"
    model_name = "fake-embedding-v1"
} | ConvertTo-Json

$AnswerResponse = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/answers" `
    -ContentType "application/json" `
    -Body $AnswerPayload

$AnswerResponse | ConvertTo-Json -Depth 20
```

Expected:

- HTTP 200
- `answer_id` is returned
- answer is persisted
- provider call is persisted

## Step 7: Inspect Observability

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/answers" |
    ConvertTo-Json -Depth 20

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/llm-provider-calls" |
    ConvertTo-Json -Depth 20

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/llm-usage/summary" |
    ConvertTo-Json -Depth 20
```

Expected:

- answer records are visible
- provider calls are visible
- usage summary reflects the grounded answer request

## Step 8: Seed Retrieval Evaluation Cases

Preview:

```bash
python scripts/seed_demo_evaluation_cases.py --dry-run
```

Create cases:

```bash
python scripts/seed_demo_evaluation_cases.py
```

Expected:

- five demo evaluation cases are created
- each case has `expected_chunk_version_ids` populated from indexed demo content
- rerun skips identical cases

## Step 9: Run Retrieval Evaluation

List cases and collect IDs dynamically:

```powershell
$Cases = Invoke-RestMethod `
    -Method Get `
    -Uri "http://localhost:8000/api/v1/evaluation/cases"

$Cases.items | Select-Object id, name, query | Format-Table

$CaseIds = @($Cases.items | Select-Object -ExpandProperty id)

$EvaluationPayload = @{
    evaluation_case_ids = $CaseIds
    top_k = 5
    provider = "fake"
    model_name = "fake-embedding-v1"
} | ConvertTo-Json

$EvaluationResponse = Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/evaluation/runs" `
    -ContentType "application/json" `
    -Body $EvaluationPayload

$EvaluationResponse.summary | Format-List
```

Inspect persisted results:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/evaluation/results" |
    ConvertTo-Json -Depth 20
```

Expected:

- `case_count = 5`
- `succeeded_count = 5`
- `failed_count = 0`
- `hit_rate_at_k` is visible
- `mean_recall_at_k` is visible
- `mean_reciprocal_rank` is visible

Exact metric values may vary with fake-embedding ranking behavior. The run should complete successfully for all seeded cases.

## Step 10: Interpret Results

- Lower fake-provider metrics are acceptable in local testing.
- Fake embeddings are deterministic but not production-grade semantic embeddings.
- The platform value is that retrieval quality is measured, persisted, and auditable.
- A future deployment can use the same evaluation framework to compare stronger embeddings, reranking, chunking changes, and retrieval parameters.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Retrieval returns empty results | demo dataset not indexed, or API using a different database | run `python scripts/seed_demo_dataset.py` and verify `DATABASE_URL` matches across CLI and API |
| Answer request returns 422 | invalid request body | use `question`, `top_k`, `provider`, and `model_name` as shown above |
| Answer request returns 500 | LLM provider misconfiguration | confirm `LLM_PROVIDER=fake` in `.env` and restart the API |
| Evaluation cases list is empty | cases not seeded | run `python scripts/seed_demo_evaluation_cases.py` after indexing |
| Evaluation misses expected chunks | retrieval ranking limitation with fake embeddings | inspect query traces and per-case `recall_at_k` / `reciprocal_rank` |

## Related Documentation

- [End-to-End Demo Guide](manual-flows/end-to-end-demo-guide.md)
- [Retrieval Evaluation Workflow](manual-flows/retrieval-evaluation-workflow.md)
- [Demo API Examples](manual-flows/api-examples.md)
- [Production Readiness Guide](../operations/production-readiness.md)
