# ADR-014: Add Grounded Answer API

## Status

Accepted

## Context

The platform already supports semantic retrieval, active vector indexing, query tracing, and trace read APIs.

The next step is to generate answers from retrieved context.

However, answer generation in a RAG system must be grounded and auditable. The platform should not simply call an LLM and trust its output.

The system needs to return:

- answer text
- answer status
- query_trace_id
- citations linked to retrieved chunks

## Decision

The system will expose:

- POST /api/v1/answers

The GroundedAnswerService will:

1. Convert the user question into a semantic retrieval query.
2. Run semantic retrieval.
3. Require query_trace_id.
4. Return insufficient_context if no chunks are retrieved.
5. Generate answer text using LLMProvider when chunks exist.
6. Build citations from retrieved chunks in backend code.
7. Return a GroundedAnswer.

The current implementation uses FakeLLMProvider.

## Why Use a Provider Boundary

The LLMProvider boundary keeps the application independent from any specific model vendor.

This allows the system to support:

- FakeLLMProvider for local tests
- OpenAI provider later
- AWS Bedrock provider later
- fallback providers later

## Why Backend-Owned Citations

The LLM does not decide citations.

The backend constructs citations from retrieved chunks.

This reduces the risk of citation hallucination and guarantees that every returned citation maps to actual retrieved context.

## Why Support insufficient_context

When retrieval returns no chunks, the system should not invent an answer.

The API returns status insufficient_context with no citations.

This is a safer default for enterprise RAG systems.

## Consequences

### Positive

- Introduces end-to-end RAG behavior.
- Keeps answer generation testable with fake providers.
- Preserves traceability through query_trace_id.
- Prevents LLM-generated fake citations.
- Creates a clean extension point for real LLM providers.

### Negative

- Answers are not persisted yet.
- FakeLLMProvider does not represent real model behavior.
- Citation verification is still basic.
- No answer-level cost tracking yet.
- No authorization or tenant scoping yet.

## Alternatives Considered

### Let the LLM Return Citations

The model could be prompted to cite sources directly.

Rejected for now because models can invent citations or cite chunks incorrectly.

### Skip insufficient_context Handling

The system could always call the LLM even with no retrieved context.

Rejected because that encourages hallucination.

### Integrate a Real LLM Immediately

A real LLM provider could be added now.

Deferred to keep this slice deterministic, cheap, and focused on architecture.

## Follow-Up

Future work should add:

- answer persistence
- answer trace records
- real LLM provider adapter
- citation verification
- LLM cost tracking
- groundedness evaluation
- provider fallback strategy