# ADR-001: Use a Modular Monolith Architecture

## Status

Accepted

## Context

The Incremental RAG Indexing Platform needs to support multiple technical capabilities:

- ingestion
- document versioning
- section extraction
- chunking
- embedding generation
- vector indexing
- retrieval
- answer generation
- evaluation
- audit logging
- cost tracking

These capabilities have clear conceptual boundaries, but they do not initially require separate deployable services.

A distributed architecture would introduce operational complexity too early.

## Decision

The system will use a modular monolith architecture.

The codebase will be organized into explicit modules and layers:

- API
- application services
- domain
- repositories
- infrastructure
- providers
- retrieval
- evaluation
- audit

The system will be deployed as a single application in early versions.

## Alternatives Considered

### Simple Layered CRUD Application

This would be faster to implement, but it would not represent the domain complexity well.

It could also lead to application services manipulating database models directly.

Rejected because the system needs stronger domain boundaries and explicit separation between application workflows, domain concepts, and infrastructure concerns.

### Microservices

Separate services could be created for ingestion, indexing, retrieval, and evaluation.

This might make sense at larger scale, but it would introduce:

- distributed transactions
- service discovery
- network failures
- duplicated deployment complexity
- more observability requirements
- harder local development

Rejected for V1 because it adds operational overhead before the core domain is proven.

### Framework-Centric RAG Application

A LangChain-first or LlamaIndex-first architecture could speed up prototyping.

However, it would make the framework the center of the design.

Rejected because the platform should own its domain model and use frameworks only as adapters later.

## Consequences

### Positive

- Clear architecture boundaries
- Simple deployment
- Easier local development
- Easier testing
- Lower operational complexity
- Easier refactoring into services later if needed

### Negative

- Requires discipline to preserve boundaries
- Modules can become coupled if not reviewed
- Scaling individual components independently is harder
- Background worker boundaries will need careful design later

## Follow-Up Decisions

Future ADRs may define:

- worker architecture
- pgvector indexing strategy
- embedding provider strategy
- query trace storage
- evaluation dataset versioning
- audit log retention