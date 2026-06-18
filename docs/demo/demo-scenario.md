# Demo Scenario

## Purpose

This document defines the end-to-end demo scenario for the Incremental RAG Indexing Platform.

The goal is to make the project demonstrable without requiring external API keys.

OpenAI integration will be added later as an optional demo mode.

## Company Context

The fictional company is Acme AI Platform.

Acme has internal engineering and operations documents that employees need to query.

The platform indexes these documents incrementally, retrieves relevant chunks, generates grounded answers with citations, records query traces, tracks LLM provider calls, reports cost and usage, and evaluates retrieval quality.

## Demo Documents

The demo dataset will include four internal documents:

1. Project Atlas Brief
2. Incident Response Playbook
3. Customer Support Escalation Policy
4. Engineering Onboarding Guide

## Demo Questions

The demo should support the following questions:

### Project Atlas

Question:

    What is Project Atlas?

Expected behavior:

- retrieve chunks from Project Atlas Brief
- answer with grounded citations
- create query trace
- create answer record
- create provider call record

Question:

    Who owns Project Atlas?

Expected behavior:

- retrieve Project Atlas ownership section
- answer with the responsible team
- include citation to the ownership chunk

### Support Escalation

Question:

    What should support do before escalating a customer issue?

Expected behavior:

- retrieve Customer Support Escalation Policy
- answer with required pre-escalation checks
- cite the escalation policy

### Incident Response

Question:

    What is the incident severity process?

Expected behavior:

- retrieve Incident Response Playbook
- explain severity levels or process
- cite incident response content

### Engineering Onboarding

Question:

    What should new engineers do in their first week?

Expected behavior:

- retrieve Engineering Onboarding Guide
- answer with first-week onboarding steps
- cite onboarding chunks

## Demo Flow

The complete manual demo should show:

1. Seed demo documents.
2. Verify indexed document versions and chunks.
3. Run semantic retrieval.
4. Inspect query trace.
5. Generate grounded answer.
6. Inspect persisted answer and citations.
7. Inspect LLM provider call records.
8. Inspect LLM usage summary.
9. Create or inspect retrieval evaluation cases.
10. Run retrieval evaluation.
11. Inspect evaluation results.

## Provider Strategy

The default demo uses fake providers.

This ensures:

- no external API key is required
- no accidental cost is incurred
- tests remain deterministic
- GitHub users can run the project locally

A real OpenAI provider can be enabled later as an optional mode.

## Non-Goals

This demo does not add:

- OpenAI real integration
- production authentication
- multi-user demo UI
- frontend
- hosted deployment
- dashboard charts

## Success Criteria

The demo is successful when a reviewer can:

- run the project locally
- seed the demo dataset
- ask a demo question
- see retrieved chunks
- see a grounded answer with citations
- inspect query trace
- inspect provider call audit records
- inspect usage and cost summary
- run retrieval evaluation
- understand the architecture from docs