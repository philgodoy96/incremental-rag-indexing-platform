# End-to-End Demo Guide

## Purpose

This guide explains how to manually demonstrate the Incremental RAG Indexing Platform using the deterministic demo dataset.

The demo is designed to show the full platform behavior:

- demo dataset validation
- document indexing
- semantic retrieval
- query trace inspection
- grounded answer generation
- persisted answers and citations
- LLM provider call auditability
- usage and cost reporting
- retrieval evaluation

The default demo uses fake providers so it can run without external API keys.

## Demo Dataset

The demo dataset is defined under:

    demo/documents

The dataset manifest is:

    demo/documents/manifest.json

The manifest defines the dataset name, version, document file paths, stable external IDs, source URIs, and tags.

## Validate Demo Dataset

Run:

    python scripts/preview_demo_dataset.py

Expected output:

    Dataset: acme_internal_knowledge_demo
    Version: 1.0.0
    Documents: 4

The output should list:

- Project Atlas Brief
- Incident Response Playbook
- Customer Support Escalation Policy
- Engineering Onboarding Guide

Each document should include:

- external_id
- source_uri
- file_path
- tags
- checksum

## Start the Application

Start the local environment using the project setup instructions.

Typical flow:

    docker compose up --build

Then verify the API is available:

    GET /health

If the project exposes Swagger UI, open:

    /docs

## Load or Index Demo Documents

Use the existing ingestion/indexing flow in the project to load the demo documents.

The important requirement is that the four demo documents become available as indexed chunks.

The documents to load are:

- demo/documents/project-atlas-brief.md
- demo/documents/incident-response-playbook.md
- demo/documents/customer-support-escalation-policy.md
- demo/documents/engineering-onboarding-guide.md

After indexing, verify that the system has document versions, chunk versions, embeddings, and vector index entries.

## Demo Question Set

Use the following demo questions:

### Project Atlas

    What is Project Atlas?

Expected retrieval target:

- Project Atlas Brief
- Overview section

Expected answer behavior:

- explain that Project Atlas is an internal knowledge intelligence initiative
- mention grounded AI answers
- cite Project Atlas Brief

### Project Ownership

    Who owns Project Atlas?

Expected retrieval target:

- Project Atlas Brief
- Ownership section

Expected answer behavior:

- identify the Platform Intelligence team
- mention Maya Chen as accountable engineering manager
- mention Jordan Lee as product lead
- cite Project Atlas Brief

### Support Escalation

    What should support do before escalating a customer issue?

Expected retrieval target:

- Customer Support Escalation Policy
- Pre-Escalation Checklist section

Expected answer behavior:

- mention account verification
- mention affected workspace
- mention reproduction or validation
- mention request IDs, timestamps, logs, screenshots, and attempted steps
- cite Customer Support Escalation Policy

### Incident Response

    What is the incident severity process?

Expected retrieval target:

- Incident Response Playbook
- Severity Levels and Response Process sections

Expected answer behavior:

- explain SEV1, SEV2, and SEV3
- mention incident commander for SEV1 and SEV2
- mention mitigation before perfect diagnosis during active impact
- cite Incident Response Playbook

### Engineering Onboarding

    What should new engineers do in their first week?

Expected retrieval target:

- Engineering Onboarding Guide
- First Week section

Expected answer behavior:

- mention local development setup
- mention running the test suite
- mention reading architecture docs
- mention reviewing recent pull requests
- mention completing a small documentation or test improvement
- cite Engineering Onboarding Guide

## Run Semantic Retrieval

Use the semantic retrieval endpoint:

    POST /api/v1/retrieval/search

Example request shape:

    {
      "query": "What is Project Atlas?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Expected behavior:

- response includes retrieved chunks
- response includes or links to a query trace identifier
- top results should come from Project Atlas Brief

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

Example request shape:

    {
      "query": "Who owns Project Atlas?",
      "top_k": 5,
      "retrieval_provider": "fake",
      "retrieval_model_name": "fake-embedding-v1",
      "llm_provider": "fake",
      "llm_model_name": "fake-llm-v1"
    }

Expected behavior:

- answer is returned
- answer includes citations
- answer is persisted
- provider call is persisted
- query trace is linked or inspectable

## Inspect Persisted Answers

Use the answer read API:

    GET /api/v1/answers
    GET /api/v1/answers/{answer_id}

Expected behavior:

- answer record exists
- citations are persisted
- answer can be audited after generation

## Inspect LLM Provider Calls

Use the LLM provider call read API:

    GET /api/v1/llm-provider-calls
    GET /api/v1/llm-provider-calls/{provider_call_id}

Expected behavior:

- provider call records exist
- records include provider and model
- records include status
- records include latency metadata when available
- records include usage metadata when available
- failed provider calls are inspectable when failures are simulated

## Inspect Usage and Cost Summary

Use the usage reporting API:

    GET /api/v1/llm-usage/summary
    GET /api/v1/llm-usage/by-model

Expected behavior:

- summary includes call_count
- summary includes succeeded_count and failed_count
- summary includes token totals when available
- summary includes estimated_cost_usd
- by-model endpoint groups by provider/model

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
- indexed chunks are available
- retrieval returns relevant chunks
- query traces explain retrieval
- grounded answers include citations
- answers and citations are persisted
- provider calls are auditable
- usage and cost reporting works
- retrieval evaluation produces metrics

## Troubleshooting

### Retrieval returns irrelevant chunks

Check:

- documents were indexed
- embeddings were generated
- vector index entries exist
- provider/model values match the indexed embeddings
- top_k is high enough

### Answer has weak citations

Check:

- retrieval returned the expected chunks
- answer generation used retrieved chunks
- citations were persisted
- fake provider behavior is deterministic and limited

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