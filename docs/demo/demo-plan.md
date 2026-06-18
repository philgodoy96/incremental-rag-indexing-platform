# Demo Plan: Dataset, Seed Data & Manual Flow

## Objective

Create a reproducible end-to-end demo flow for the Incremental RAG Indexing Platform.

This demo turns the project from a strong backend and AI infrastructure implementation into a reliably demonstrable system.

## Why This Demo Exists

The project already has important backend and AI infrastructure capabilities.

However, a reviewer needs a clean way to see the system working.

This demo introduces:

- deterministic demo documents
- seed data
- retrieval evaluation cases
- manual demo flow
- Postman or cURL guide
- demo documentation

## Provider Strategy

The demo uses fake providers by default.

This keeps the project:

- free to run
- deterministic
- testable without external services
- safe for public GitHub usage

Real provider integration is documented separately and is not required for the default demo workflow.

This keeps two concerns separate:

- reproducible local demo data and workflow
- optional external provider validation and cost

## Implemented Demo Assets

The following demo assets are in place:

- end-to-end demo scenario documentation
- deterministic demo documents under `demo/documents/`
- demo dataset preview and seed scripts
- retrieval evaluation case seeding
- manual demo walkthroughs and API examples
- optional provider comparison and smoke-test guides

## Optional Follow-Up

Optional follow-up work includes:

- additional provider comparison observations
- latency, token, and cost observations during controlled validation
- answer quality and citation quality observations
- retrieval evaluation baselines across embedding strategies