# Incremental RAG Indexing Platform

A production-style backend platform for incremental Retrieval-Augmented Generation indexing.

This project focuses on building the infrastructure behind reliable enterprise RAG systems: document versioning, structure-aware chunking, embedding reuse, vector retrieval, grounded answers with citations, retrieval evaluation, cost tracking, and auditability.

This is not a chatbot demo.  
It is an AI infrastructure project focused on retrieval correctness, operational traceability, and production-minded backend design.

## Why This Project Exists

Many simple RAG systems reprocess entire documents whenever content changes.

That approach becomes expensive and difficult to audit as knowledge bases grow.

A production-grade RAG indexing platform should be able to answer questions such as:

- What changed in a document?
- Which document version introduced the change?
- Which sections and chunks were affected?
- Which chunks need new embeddings?
- Which embeddings can be reused?
- Which retrieved evidence supported an answer?
- Which retrieval strategy was used?
- Did retrieval quality improve or regress after a change?
- How much did indexing cost?

This project is designed around those questions.

## Core Capabilities

Planned V1 capabilities include:

- Local Markdown document ingestion
- Immutable document versioning
- Section extraction
- Structure-aware chunking
- Chunk-level hashing
- Embedding input hashing
- Fake deterministic embeddings
- PostgreSQL persistence
- pgvector-based semantic search
- Keyword search
- Hybrid retrieval
- Grounded answers with citations
- Query tracing
- Audit logs
- Retrieval evaluation
- Cost tracking
- Indexing dry runs
- Prompt injection risk detection

## Architecture Style

The project uses a modular monolith architecture with explicit boundaries between:

- API layer
- Application services
- Domain layer
- Repository interfaces
- Infrastructure repositories
- Database models
- Provider adapters
- Retrieval layer
- Evaluation layer
- Audit layer

The domain model is intentionally separated from SQLAlchemy models.

Application services operate on domain entities and repository contracts, not directly on database models.

## Tech Stack

Core stack:

- Python
- FastAPI
- PostgreSQL
- pgvector
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- pytest
- Docker
- Docker Compose

Initial provider strategy:

- FakeEmbeddingProvider first
- FakeLLMProvider first
- OpenAI or AWS Bedrock providers later

Observability roadmap:

- Prometheus
- Grafana
- OpenTelemetry
- Sentry

Future adapters:

- LangChain adapter
- LlamaIndex adapter

These adapters are planned as integration boundaries, not as the core architecture.

## Source of Truth vs Derived Data

The system distinguishes durable facts from rebuildable or derived artifacts.

Source of truth:

- SourceDocument
- DocumentVersion
- SectionVersion
- ChunkVersion

Derived artifacts:

- EmbeddingRecord
- EmbeddingCostRecord

Projections:

- VectorIndexEntry

Operational data:

- IngestionRun
- IngestionJob
- QueryTrace
- AuditLogEntry
- EvaluationRun
- EvaluationResult

User-facing data:

- GeneratedAnswer
- AnswerCitation
- AnswerFeedback

This distinction is central to the system's auditability and rebuildability.

## Seed Document Strategy

The first source system will be local Markdown documents stored under:

    seed_documents/

These documents will simulate realistic enterprise knowledge such as:

- project status reports
- operational runbooks
- architecture decision records
- ownership matrices
- incident response guides
- retrieval evaluation guides
- prompt injection test documents

Seed documents are part of the system design and testing strategy. They are introduced gradually as ingestion, versioning, chunking, retrieval, and evaluation capabilities are implemented.

## Planned Milestones

1. Project foundation and architecture documentation
2. Application scaffold with FastAPI, Docker, PostgreSQL, and tests
3. Local Markdown ingestion
4. Document and section versioning
5. Structure-aware chunking
6. Fake deterministic embeddings
7. pgvector semantic search
8. Keyword and hybrid retrieval
9. Grounded answers with citations
10. Prompt injection risk detection
11. Query tracing and audit logs
12. Retrieval evaluation
13. Cost tracking and dry-run indexing
14. Real embedding and LLM providers
15. Worker-based ingestion and advanced reliability patterns

## Repository Status

Current status:

- Project foundation documentation completed
- FastAPI application scaffold introduced
- Docker development environment introduced
- PostgreSQL with pgvector prepared for persistence
- SQLAlchemy engine and session foundation introduced
- Alembic migration environment introduced
- Database readiness endpoint available
- SourceDocument and DocumentVersion domain foundation introduced
- Initial document persistence tables introduced
- Local Markdown discovery endpoint introduced
- Persistent local seed ingestion endpoint introduced
- Initial seed documents committed
- Markdown section extraction introduced
- SectionVersion persistence introduced

## Documentation

Key documentation areas:

    docs/architecture/
    docs/adr/
    docs/experiments/
    docs/reviews/

Architecture documents explain how the system works.

ADRs explain why important technical decisions were made.

Experiment documents will track retrieval and evaluation changes.

Engineering reviews will capture reliability, scaling, and operational analysis.

## Design Priorities

This project optimizes for:

- correctness
- maintainability
- traceability
- auditability
- cost awareness
- retrieval quality
- operational reliability
- professional backend architecture