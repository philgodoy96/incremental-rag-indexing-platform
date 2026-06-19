# System Overview

## Purpose

The Incremental RAG Indexing Platform is a backend system for ingesting, versioning, indexing, retrieving, evaluating, and auditing enterprise knowledge.

The system is designed to support grounded AI answers with citations while avoiding unnecessary re-indexing of unchanged content.

## Business Context

Enterprise knowledge changes continuously.

Documents are updated, sections are renamed, runbooks evolve, architectural decisions change, and incident procedures improve.

A naive RAG system often reprocesses entire documents whenever anything changes.

This is inefficient, expensive, and difficult to audit.

This platform is designed around the idea that a reliable RAG system should understand change at multiple levels:

- source document
- document version
- section version
- chunk version
- embedding input
- vector index entry

## Primary Users

### Platform Engineers

Platform engineers use the system to ingest and maintain internal knowledge.

They care about:

- indexing correctness
- failure recovery
- cost control
- traceability through persisted query traces, answers, and provider calls
- rebuildability

### Applied AI Engineers

Applied AI engineers use the system to improve retrieval quality and answer grounding.

They care about:

- chunking strategy
- retrieval strategies
- evaluation metrics
- query traces
- future prompt-injection hardening

### Internal Users

Internal users ask questions and expect grounded answers.

They care about:

- answer usefulness
- citations
- transparency
- no-evidence responses when evidence is insufficient

## High-Level Responsibilities

The current repository implements:

1. Ingesting local Markdown documents.
2. Detecting document changes.
3. Creating immutable document versions.
4. Extracting section versions from document versions.
5. Creating deterministic chunk versions from section versions.
6. Generating embeddings for new or changed chunks.
7. Avoiding duplicate embedding generation where reuse applies.
8. Maintaining a rebuildable vector index.
9. Semantic retrieval over the active vector index.
10. Generating grounded answers with citations.
11. Capturing query traces.
12. Running retrieval evaluation.
13. Tracking estimated embedding cost through persisted cost records.
14. Persisting LLM provider calls, answers, citations, and evaluation results for auditability.

Recommended future hardening includes keyword and hybrid retrieval, dedicated audit-log persistence, and automated prompt-injection risk detection.

## Out of Scope for the Current Repository

The following are not part of the current application surface:

- multi-tenancy
- authentication
- authorization
- external document sources beyond local Markdown seed/demo flows
- background workers
- RabbitMQ, Redis, or Kafka-backed job queues
- LangChain or LlamaIndex as the core architecture
- fine-tuning
- UI or frontend
- real-time collaboration
- bundled Prometheus, Grafana, OpenTelemetry, Sentry, or Datadog dashboards

These may be added later.

## Architecture Style

The system is a modular monolith.

This provides:

- clear boundaries
- simple deployment
- easier local development
- realistic production structure without distributed-system overhead too early
- a path to extract services later if needed

## Major Modules

### API Layer

Exposes HTTP endpoints through FastAPI.

Current examples:

- ingestion runs
- indexing dry runs
- retrieval search
- query trace read APIs
- answer generation and answer read APIs
- provider call read APIs
- LLM usage reporting
- evaluation runs

### Application Layer

Coordinates use cases.

Application services define workflows such as:

- ingest local documents
- extract document structure
- chunk changed sections
- generate missing embeddings
- rebuild vector index
- execute retrieval
- generate grounded answers
- run evaluation

### Domain Layer

Contains domain entities, value objects, enums, and business invariants.

The domain layer should not depend on FastAPI, SQLAlchemy, pgvector, OpenAI, or any specific infrastructure tool.

### Repository Layer

Defines interfaces for persistence.

Application services depend on repository contracts, not database implementation details.

### Infrastructure Layer

Implements persistence, SQLAlchemy models, database sessions, provider clients, and external integrations.

### Provider Layer

Defines adapters for embedding providers and LLM providers.

The default providers are fake and deterministic for local development and CI.

An optional OpenAI LLM adapter exists behind the same provider boundary. Embedding generation currently uses the fake embedding provider.

### Retrieval Layer

Implements semantic search, scoring, filtering, and query tracing.

Keyword and hybrid retrieval are planned future hardening, not current functionality.

### Evaluation Layer

Runs evaluation cases against retrieval strategies and computes metrics.

## System Flow

    Local Markdown Document
            |
            v
    SourceDocument
            |
            v
    DocumentVersion
            |
            v
    SectionVersion
            |
            v
    ChunkVersion
            |
            v
    EmbeddingRecord
            |
            v
    VectorIndexEntry
            |
            v
    RetrievalResult
            |
            v
    GeneratedAnswer + AnswerCitation

## Reliability Design Targets

The system is designed toward:

- idempotent indexing
- no duplicate embeddings where reuse applies
- provider failure capture and auditability
- vector index rebuilds from durable records
- auditability of important operations through persisted traces, answers, and provider calls

Automatic retry/backoff, circuit breakers, and provider fallback are not implemented in the current codebase.

## Observability

### Product and Retrieval Observability (Implemented)

Captured through domain records such as:

- QueryTrace
- EvaluationRun summaries and persisted evaluation results
- EmbeddingCostRecord
- LLMProviderCallRecord
- AnswerRecord and AnswerCitationRecord

Usage summary and by-model reporting APIs aggregate provider call metadata.

### Technical Execution Observability (Future Hardening)

Future deployment hardening may use:

- OpenTelemetry
- Prometheus
- Grafana
- Sentry

QueryTrace is not a replacement for OpenTelemetry.

OpenTelemetry would explain execution.

QueryTrace explains retrieval decisions.

## Security Goals

The system should treat retrieved content as untrusted evidence.

Retrieved chunks must not be treated as instructions.

Future hardening may detect suspicious prompt injection patterns and persist risk flags. Chunk versions can store risk-flag metadata, but automated detection is not part of the current application flow.

## Key Design Tension

The main engineering trade-off is between simplicity and traceability.

A simple RAG system could store only current document text and current embeddings.

This project intentionally adds versioning, auditability, and evaluation because production-minded RAG systems require trustworthy behavior over time.
