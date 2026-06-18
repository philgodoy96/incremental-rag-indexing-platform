# End-to-End Demo Guide

## Purpose

This guide explains how to manually demonstrate the Incremental RAG Indexing Platform using the deterministic demo dataset.

The demo is designed to show the full platform behavior:

- demo dataset validation
- manifest-driven indexing
- document versioning
- chunking
- embedding generation
- vector index projection
- semantic retrieval
- query trace inspection
- grounded answer generation
- persisted answers and citations
- LLM provider call auditability
- usage and cost reporting
- retrieval evaluation

The default demo uses fake providers so it can run without external API keys.

## Demo Dataset

The deterministic demo dataset is defined under:

    demo/documents

The dataset manifest is:

    demo/documents/manifest.json

The manifest defines:

- dataset name
- dataset version
- document file paths
- stable external IDs
- source URIs
- titles
- tags

The demo documents are:

- Project Atlas Brief
- Incident Response Playbook
- Customer Support Escalation Policy
- Engineering Onboarding Guide

## Validate Demo Dataset Without Database Writes

Run:

    python scripts/preview_demo_dataset.py

Expected behavior:

- dataset name is printed
- dataset version is printed
- four demo documents are listed
- each document has a checksum

This command does not write to the database.

## Preview Demo Indexing Without Database Writes

Run:

    python scripts/seed_demo_dataset.py --dry-run

Expected behavior:

- manifest is loaded
- demo documents are discovered
- no source documents are persisted
- no chunks are created
- no embeddings are created
- no vector index entries are created

Use this before running the real seed command.

## Index Demo Dataset

Ensure Postgres is running and migrations are applied.

Typical local flow:

    docker compose up -d postgres
    python -m alembic upgrade head
    python scripts/seed_demo_dataset.py

Expected behavior on first run:

- four demo documents are discovered
- four source documents are created or updated
- document versions are created
- sections and chunks are created
- fake embeddings are generated
- current vector index entries are projected

Expected behavior on unchanged rerun:

- documents are skipped as unchanged
- no duplicate document versions are created
- existing vector index entries remain available

## Why This Command Exists

The preview command only validates files from disk.

The seed command sends the deterministic demo dataset through the real ingestion pipeline:

    DemoDatasetDiscoveryService
        -> LocalSeedDocumentIngestionService
        -> document ingestion transaction
        -> chunking
        -> embedding
        -> vector index projection

The command should not duplicate ingestion logic.

It should not manually insert vector index rows.

## Provider Configuration

The retrieval provider and retrieval model are selected in request bodies using:

- provider
- model_name

The LLM provider is selected through runtime environment configuration:

    LLM_PROVIDER=fake

or:

    LLM_PROVIDER=openai

The answer request body should not include `llm_provider`, `llm_model_name`, `retrieval_provider`, or `retrieval_model_name`.

For the default local demo, use:

    LLM_PROVIDER=fake

## Run Semantic Retrieval

Use the semantic retrieval endpoint:

    POST /api/v1/retrieval/search

Example request:

    {
      "query": "Who owns Project Atlas?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Expected behavior after demo indexing:

- response includes retrieval results
- response includes a query trace identifier
- at least one top_k result should reference Project Atlas content
- `project-atlas-brief/ownership` should be retrievable for ownership questions

Example successful result characteristics:

- `results` is not empty
- result items include vector_index_entry_id
- result items include chunk_version_id
- result items include content
- result items include heading_context
- result items include distance

## Known Fake Embedding Limitation

The fake embedding provider is deterministic and useful for local testing, but it is not a high-quality semantic model.

This means the correct chunk may appear in top_k without always ranking first.

For example, a query like:

    Who owns Project Atlas?

may retrieve the Project Atlas ownership chunk in the top_k results while another unrelated chunk ranks above it.

This is acceptable for the fake-provider demo.

It is also why the platform includes retrieval evaluation APIs and query tracing.

A production embedding provider should improve ranking quality.

## Inspect Query Trace

Use the query trace read API:

    GET /api/v1/retrieval/traces
    GET /api/v1/retrieval/traces/{query_trace_id}

Expected behavior:

- trace exists for the retrieval request
- trace includes query text
- trace includes provider/model metadata
- trace includes hit records
- trace helps explain why chunks were selected

## Generate Grounded Answer

Use the grounded answer endpoint:

    POST /api/v1/answers

Example request:

    {
      "question": "Who owns Project Atlas?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Expected behavior with `LLM_PROVIDER=fake`:

- response returns HTTP 200
- answer is persisted
- provider call is persisted
- usage summary is updated
- citations are available when retrieved context exists

If retrieval returns context but the fake embedding ranking is imperfect, the fake answer may summarize the highest-ranked chunk rather than the ideal chunk.

That is a retrieval quality issue, not an ingestion failure.

## Inspect Persisted Answers

Use the answer read API:

    GET /api/v1/answers
    GET /api/v1/answers/{answer_id}

Expected behavior:

- latest answer record exists
- status is inspectable
- query_trace_id is available
- provider/model metadata is available

## Inspect LLM Provider Calls

Use the LLM provider call read API:

    GET /api/v1/llm-provider-calls
    GET /api/v1/llm-provider-calls/{provider_call_id}

Expected behavior:

- provider call records exist
- successful fake calls have provider `fake`
- fake calls should have model `fake-llm-v1`
- failed real provider calls are persisted with error messages
- failed real provider calls may have answer_id set to null

A failed OpenAI call caused by rate limits is still a useful observability signal.

It proves failed provider calls are captured, but it does not prove successful real-provider answer generation.

## Inspect Usage and Cost Summary

Use the usage reporting API:

    GET /api/v1/llm-usage/summary
    GET /api/v1/llm-usage/by-model

Expected behavior:

- summary includes call_count
- summary includes succeeded_count
- summary includes failed_count
- summary includes token totals when available
- summary includes estimated_cost_usd
- by-model endpoint groups by provider and model

For fake provider calls, estimated cost is expected to be zero.

For failed OpenAI calls with no usage metadata, token totals may remain zero.

## Demo Question Set

Use the following demo questions.

### Project Atlas

    What is Project Atlas?

Expected retrieval target:

- Project Atlas Brief
- Overview section

### Project Ownership

    Who owns Project Atlas?

Expected retrieval target:

- Project Atlas Brief
- Ownership section

Expected answer behavior with strong retrieval:

- identify the Platform Intelligence team
- mention Maya Chen as accountable engineering manager
- mention Jordan Lee as product lead
- cite Project Atlas Brief

### Support Escalation

    What should support do before escalating a customer issue?

Expected retrieval target:

- Customer Support Escalation Policy
- Pre-Escalation Checklist section

### Incident Response

    What is the incident severity process?

Expected retrieval target:

- Incident Response Playbook
- Severity Levels and Response Process sections

### Engineering Onboarding

    What should new engineers do in their first week?

Expected retrieval target:

- Engineering Onboarding Guide
- First Week section

## Run Retrieval Evaluation

Use the retrieval evaluation APIs.

First create or inspect evaluation cases:

    POST /api/v1/evaluation/cases
    GET /api/v1/evaluation/cases

Then run evaluation:

    POST /api/v1/evaluation/runs

Example request shape:

    {
      "evaluation_case_ids": ["evaluation-case-id"],
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Expected behavior:

- evaluation case results are persisted
- summary includes case_count
- summary includes hit_count
- summary includes hit_rate_at_k
- summary includes mean_recall_at_k
- summary includes mean_reciprocal_rank

## Demo Success Criteria

The demo is successful when the reviewer can verify:

- demo documents exist and are deterministic
- demo dataset can be previewed without DB writes
- demo dataset can be indexed through the real pipeline
- vector index entries are available
- retrieval returns chunks
- query traces explain retrieval
- grounded answers can be generated
- answers are persisted
- provider calls are auditable
- failed provider calls are auditable
- usage and cost reporting works
- retrieval evaluation produces metrics

## Troubleshooting

### Retrieval returns no chunks

Check:

- `python scripts/seed_demo_dataset.py` was run
- Postgres was running during seeding
- migrations were applied
- vector index entries exist
- provider/model values match indexed embeddings
- top_k is high enough

### Answer returns insufficient context

Check:

- retrieval returned context
- vector index entries are not empty
- the demo documents were indexed before answer generation

### Answer returns HTTP 422

Check the request body.

The Answer API expects:

    {
      "question": "Who owns Project Atlas?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

It does not accept answer requests using `query`, `llm_provider`, `llm_model_name`, `retrieval_provider`, or `retrieval_model_name`.

### Answer returns HTTP 500

Check runtime provider configuration.

If using fake provider:

    LLM_PROVIDER=fake

If using OpenAI provider:

    LLM_PROVIDER=openai
    OPENAI_API_KEY=your-local-secret

A common configuration error is using `OPEN_AI_API_KEY` instead of `OPENAI_API_KEY`.

### OpenAI calls fail with rate limit

This means the real provider request reached OpenAI but was rejected by provider limits.

The failure should be persisted as a failed provider call.

This does not prove successful real-provider answer generation.

Switch back to fake provider for local demo reliability:

    LLM_PROVIDER=fake

### Usage summary is empty

Check:

- answer generation was executed
- provider call persistence is enabled
- provider call records were created
- filters are not too restrictive

### Evaluation returns zero hits

Check:

- expected_chunk_version_ids reference real chunk versions
- demo documents were indexed before cases were created
- retrieval provider/model matches indexed embeddings
- top_k is large enough