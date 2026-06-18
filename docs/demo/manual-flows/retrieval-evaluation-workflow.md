# Demo Retrieval Evaluation Workflow

## Purpose

This guide explains how to run retrieval evaluation against the deterministic demo dataset.

The goal is to make retrieval quality measurable.

A RAG platform should not rely only on manual inspection of answers. If retrieval ranking gets worse, grounded answer quality will degrade even when the LLM provider is working correctly.

The demo evaluation workflow helps answer questions such as:

- Did retrieval return the expected chunk?
- Did the expected chunk appear in top_k?
- Was the expected chunk ranked first?
- Did retrieval quality regress after changing chunking or embeddings?
- Are weak answers caused by retrieval ranking or by answer generation?

## Why This Matters

During local testing, the fake embedding provider may retrieve the correct chunk in top_k without ranking it first.

For example:

    Who owns Project Atlas?

The expected chunk is:

    project-atlas-brief/ownership

With fake embeddings, that chunk may appear in top_k but not at rank 1.

This is not an ingestion failure.

It is a retrieval quality signal.

The evaluation framework turns that signal into metrics.

## Prerequisites

Before seeding evaluation cases, the demo dataset must be indexed.

Run:

    docker compose up -d postgres
    python -m alembic upgrade head
    python scripts/seed_demo_dataset.py

The dataset indexing command should create:

- source documents
- document versions
- section versions
- chunk versions
- fake embeddings
- active vector index entries

If vector index entries do not exist, evaluation case seeding will fail because expected stable section keys cannot be resolved into chunk version IDs.

## Seed Demo Evaluation Cases

Preview the operation without database writes:

    python scripts/seed_demo_evaluation_cases.py --dry-run

Create the cases:

    python scripts/seed_demo_evaluation_cases.py

Run it again to validate idempotency:

    python scripts/seed_demo_evaluation_cases.py

Expected behavior:

- first run creates the demo evaluation cases
- unchanged rerun skips identical cases
- no duplicate case names are silently created

## Demo Evaluation Cases

The demo defines five deterministic cases.

| Case | Query | Expected stable section key |
|---|---|---|
| Project Atlas ownership | Who owns Project Atlas? | project-atlas-brief/ownership |
| Project Atlas overview | What is Project Atlas? | project-atlas-brief/overview |
| Support escalation checklist | What should support do before escalating a customer issue? | customer-support-escalation-policy/pre-escalation-checklist |
| Incident severity levels | What is the incident severity process? | incident-response-playbook/severity-levels, incident-response-playbook/response-process |
| Engineering first week | What should new engineers do in their first week? | engineering-onboarding-guide/first-week |

The seed command resolves stable section keys into current chunk version IDs after indexing.

The repository should not hardcode database UUIDs.

## List Evaluation Cases

Start the API with fake provider configuration:

    LLM_PROVIDER=fake

Then call:

    GET /api/v1/evaluation/cases

PowerShell example:

    $Cases = Invoke-RestMethod `
        -Method Get `
        -Uri "http://localhost:8000/api/v1/evaluation/cases"

    $Cases.items | Select-Object id,name,query | Format-Table

Expected behavior:

- five demo evaluation cases are listed
- each case has expected_chunk_version_ids
- tags include `demo` and `retrieval-evaluation`

## Run Evaluation

Use all seeded demo cases:

    $Cases = Invoke-RestMethod `
        -Method Get `
        -Uri "http://localhost:8000/api/v1/evaluation/cases"

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

    $EvaluationResponse | ConvertTo-Json -Depth 20

Expected behavior:

- evaluation run succeeds
- each case produces a result
- result metrics are persisted
- summary metrics are returned

## Inspect Persisted Results

Call:

    GET /api/v1/evaluation/results

PowerShell example:

    Invoke-RestMethod `
        -Method Get `
        -Uri "http://localhost:8000/api/v1/evaluation/results" |
        ConvertTo-Json -Depth 20

Expected behavior:

- persisted results are listed
- each result includes expected_chunk_version_ids
- each result includes retrieved_chunk_version_ids
- each result includes recall_at_k
- each result includes reciprocal_rank

## Metric Interpretation

### hit_count

The number of expected chunk IDs that appeared in the retrieved top_k results.

If expected chunks are:

    [A]

and retrieved chunks are:

    [X, Y, A]

then:

    hit_count = 1

### recall_at_k

The fraction of expected chunks retrieved within top_k.

If a case expects two chunks and retrieval returns one of them:

    recall_at_k = 0.5

If a case expects one chunk and retrieval returns it:

    recall_at_k = 1.0

If retrieval misses all expected chunks:

    recall_at_k = 0.0

### reciprocal_rank

The inverse of the rank of the first relevant result.

If the first expected chunk appears at rank 1:

    reciprocal_rank = 1.0

If it appears at rank 3:

    reciprocal_rank = 0.3333

If no expected chunk appears:

    reciprocal_rank = 0.0

This metric helps distinguish "retrieved but ranked poorly" from "not retrieved at all."

## Example Fake Provider Observation

A local fake-provider evaluation run may produce results like:

    case_count = 5
    succeeded_count = 5
    failed_count = 0
    hit_count = 2
    total_expected_count = 6
    hit_rate_at_k = 0.4
    mean_recall_at_k = 0.3
    mean_reciprocal_rank = 0.2667

This is useful.

It shows the system can measure retrieval quality instead of assuming quality from a single answer.

The fake provider is deterministic and safe, but it is not expected to behave like a production-grade semantic embedding model.

## How To Explain Low Fake-Provider Metrics

Low fake-provider retrieval metrics should be explained as an intentional local testing limitation.

The platform value is not that fake embeddings are excellent.

The platform value is that retrieval quality is measurable, persisted, and auditable.

In a production setting, this same evaluation framework can be used to compare:

- embedding providers
- chunking strategies
- top_k values
- filtering strategies
- reranking strategies
- query rewriting strategies

## Demo Success Criteria

The demo retrieval evaluation workflow is successful when:

- demo documents are indexed
- evaluation cases are seeded
- cases resolve stable section keys into chunk version IDs
- evaluation run succeeds
- results are persisted
- summary metrics are returned
- weak fake-provider ranking is visible through metrics

## Troubleshooting

### No evaluation cases are listed

Run:

    python scripts/seed_demo_evaluation_cases.py

Then call:

    GET /api/v1/evaluation/cases

### Evaluation case seeding fails with missing section keys

Run:

    python scripts/seed_demo_dataset.py

Then rerun:

    python scripts/seed_demo_evaluation_cases.py

This usually means the demo dataset was not indexed before seeding evaluation cases.

### Evaluation cases are listed but run fails

Check:

- provider is `fake`
- model_name is `fake-embedding-v1`
- vector index entries exist
- migrations are applied
- API is connected to the same database as the scripts

### Evaluation metrics are low

Inspect query traces and retrieved_chunk_version_ids.

Low metrics with fake embeddings may be expected.

The important question is whether the framework made the weakness visible.