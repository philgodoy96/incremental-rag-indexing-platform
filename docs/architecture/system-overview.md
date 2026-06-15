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
- audit logs
- rebuildability

### Applied AI Engineers

Applied AI engineers use the system to improve retrieval quality and answer grounding.

They care about:

- chunking strategy
- retrieval strategies
- evaluation metrics
- query traces
- prompt injection risks

### Internal Users

Internal users ask questions and expect grounded answers.

They care about:

- answer usefulness
- citations
- transparency
- no-evidence responses when evidence is insufficient

## High-Level Responsibilities

The system is responsible for:

1. Ingesting local Markdown documents.
2. Detecting document changes.
3. Creating immutable document versions.
4. Extracting section versions from document versions.
5. Creating deterministic chunk versions from section versions.
6. Generating embeddings for new or changed chunks.
7. Avoiding duplicate embedding generation.
8. Maintaining a rebuildable vector index.
9. Supporting keyword, semantic, and hybrid retrieval.
10. Generating grounded answers with citations.
11. Capturing query traces.
12. Running retrieval evaluation.
13. Tracking estimated embedding cost.
14. Persisting audit logs.
15. Detecting suspicious prompt injection patterns in retrieved evidence.

## Non-Responsibilities in V1

The system will not initially support:

- multi-tenancy
- authentication
- authorization
- external document sources
- background workers
- RabbitMQ
- LangChain as the core architecture
- LlamaIndex as the core architecture
- fine-tuning
- UI
- real-time collaboration

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

Examples:

- ingestion runs
- indexing dry runs
- retrieval search
- answer generation
- evaluation runs
- audit log listing

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

The first providers will be fake and deterministic.

Real providers come later.

### Retrieval Layer

Implements keyword search, semantic search, hybrid search, scoring, filtering, and query tracing.

### Evaluation Layer

Runs evaluation cases against retrieval strategies and computes metrics.

### Audit Layer

Persists important domain and operational events.

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

## Reliability Goals

The system should support:

- safe retries
- idempotent indexing
- no duplicate embeddings
- provider failure handling
- partial failure recovery
- vector index rebuilds
- auditability of important operations

## Observability Goals

The system should expose two different types of observability.

### Product and Retrieval Observability

Captured through domain records such as:

- QueryTrace
- EvaluationRun
- AuditLogEntry
- EmbeddingCostRecord

### Technical Execution Observability

Future versions may use:

- OpenTelemetry
- Prometheus
- Grafana
- Sentry

QueryTrace is not a replacement for OpenTelemetry.

OpenTelemetry explains execution.

QueryTrace explains retrieval decisions.

## Security Goals

The system should treat retrieved content as untrusted evidence.

Retrieved chunks must not be treated as instructions.

The system should detect suspicious prompt injection patterns and persist risk flags.

## Key Design Tension

The main engineering trade-off is between simplicity and traceability.

A simple RAG system could store only current document text and current embeddings.

This project intentionally adds versioning, auditability, and evaluation because production RAG systems require trustworthy behavior over time.