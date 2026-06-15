# Engineering Guide

This guide defines the engineering standards used in this repository.

The goal is to keep the project understandable, testable, reviewable, and maintainable as it evolves.

## Engineering Principles

### 1. Design Before Implementation

Implementation should begin only after the relevant design questions are clear:

- What business problem does this slice solve?
- What are the system responsibilities?
- What entities are involved?
- What invariants must hold?
- What can fail?
- What are the API boundaries?
- How will this scale?
- How will this be tested?
- How can this be rolled back or retried?

### 2. Preserve Architecture Boundaries

The system uses a modular monolith.

Application services coordinate use cases.

Domain entities represent business concepts.

Repository interfaces define persistence contracts.

Infrastructure implements database access, provider integrations, and external tooling.

SQLAlchemy models are persistence models, not domain entities.

### 3. Make State Categories Explicit

Every important record should fit into one of these categories:

- source of truth
- derived artifact
- projection
- operational data
- user-facing data

This distinction helps determine what must be preserved, what can be rebuilt, and what can be reused.

### 4. Prefer Determinism

The following behaviors should be deterministic whenever possible:

- checksum calculation
- section extraction
- chunking
- chunk hashing
- embedding input hashing
- fake embeddings
- evaluation metrics

Determinism makes the system easier to test and reason about.

### 5. Treat Retrieved Content as Untrusted Evidence

Retrieved documents are evidence, not instructions.

The answer generation layer must not allow retrieved content to override system behavior.

Suspicious prompt injection patterns should be detected, flagged, logged, and tested.

### 6. Avoid Framework-Centric Architecture

LangChain and LlamaIndex may be added later as adapters.

They must not define the domain model, persistence model, or application service architecture.

The platform owns its retrieval and indexing architecture.

## Development Workflow

Work should be organized into focused branches.

Examples:

    docs/project-foundation
    chore/application-scaffold
    feat/local-seed-ingestion
    feat/document-versioning
    feat/section-versioning
    feat/chunk-versioning
    feat/fake-embedding-indexing
    feat/hybrid-retrieval
    feat/grounded-answers
    feat/retrieval-evaluation

Each branch should represent a coherent engineering slice.

A slice may contain multiple commits when each commit has a clear purpose.

## Commit Standards

Commit messages should explain intent.

Good examples:

    docs: add project foundation overview
    docs: define source of truth and derived artifacts
    feat: add source document domain entity
    feat: implement local markdown ingestion service
    test: cover checksum change detection
    docs: record modular monolith architecture decision

Avoid vague commit messages such as:

    update
    changes
    fixes
    wip
    stuff

## Pull Request Standards

Even when working individually, each slice should be reviewable like a pull request.

A good PR description should include:

- summary
- changes
- testing performed
- risks
- follow-up work

## Testing Expectations

Testing should include:

- unit tests
- integration tests where appropriate
- manual API testing through Swagger or Postman
- edge case testing
- failure simulation
- idempotency checks
- regression checks for retrieval behavior

Documentation-only slices should still be reviewed for:

- consistency
- accuracy
- terminology
- architectural alignment
- absence of misleading implementation claims

## Engineering Review Questions

At the end of major implementation milestones, review:

- What happens under concurrency?
- What happens if indexing crashes?
- What happens if the embedding provider fails?
- Is the operation idempotent?
- Can the vector index be rebuilt?
- What data is source of truth?
- What data is derived?
- Where are the bottlenecks?
- How is cost controlled?
- How would rollback work?

## Conceptual Review Questions

After implementation reviews, validate the underlying concepts.

Examples:

- Why version chunks instead of overwriting them?
- Why should answers cite ChunkVersions instead of documents?
- Why is QueryTrace different from OpenTelemetry?
- Why are embeddings derived artifacts but still worth preserving?
- What makes hybrid retrieval different from semantic search?
- How can prompt injection affect a RAG system?
- How does evaluation detect retrieval regressions?

Incomplete explanations should be revisited until the trade-offs are clear.

## Documentation Standards

Required documentation areas:

    docs/architecture/
    docs/adr/
    docs/experiments/
    docs/reviews/

Architecture documents explain system design.

ADRs explain major technical decisions.

Experiment documents track retrieval and evaluation changes.

Review documents capture engineering analysis after milestones.

## Seed Document Standards

Seed documents must be realistic and intentional.

They should help test capabilities such as:

- ingestion
- document versioning
- section extraction
- chunking
- incremental indexing
- retrieval
- citations
- evaluation
- prompt injection detection

Seed documents should be introduced only when the system has the capability to process them.

## Operational Mindset

The system should be designed as if it could eventually run in production.

Important questions:

- Can this operation be retried safely?
- What is persisted before and after provider calls?
- What happens if a process dies halfway?
- How are stale indexes detected?
- How are duplicate embeddings prevented?
- How can an answer be explained to a user or auditor?
- How is retrieval quality measured over time?
- How are cost surprises prevented?