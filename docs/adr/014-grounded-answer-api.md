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
2. Run semantic retrieval and retain an immutable retrieval snapshot.
3. Require query_trace_id.
4. Return insufficient_context if no chunks are retrieved.
5. Generate a structured answer draft using LLMProvider when chunks exist.
6. Require the model to propose provenance citations with stable candidate
   references and verbatim evidence spans.
7. Validate proposed provenance deterministically in application code.
8. Persist and return only validated provenance as a GroundedAnswer.

See ADR-023 for the provenance vs semantic entailment boundary.

The current default implementation uses FakeLLMProvider.

## Why Use a Provider Boundary

The LLMProvider boundary keeps the application independent from any specific model vendor.

This allows the system to support:

- FakeLLMProvider for local tests
- OpenAI provider later
- AWS Bedrock provider later
- fallback providers later

## Why Application-Validated Provenance

The model may propose provenance. The model may not establish provenance.

The application establishes provenance by checking that each proposed citation:

- references a candidate in the exact retrieval snapshot used for generation
- includes a non-empty evidence span that occurs verbatim in that candidate

This prevents invented candidate references from being published, while still
recording which evidence the model selected rather than attaching every
retrieved chunk automatically.

## Why Support insufficient_context

When retrieval returns no chunks, the system should not invent an answer.

The API returns status insufficient_context with no citations.

This is a safer default for enterprise RAG systems.

## Consequences

### Positive

- Introduces end-to-end RAG behavior.
- Keeps answer generation testable with fake providers.
- Preserves traceability through query_trace_id.
- Prevents publishing invented candidate references.
- Creates a clean extension point for real LLM providers.

### Negative

- Invalid model-proposed provenance fails closed and blocks answer publication.
  The API surfaces that as HTTP 502 Bad Gateway. Completed provider usage is
  still persisted with `answer_id=None`.
- Verbatim provenance validation does not prove semantic entailment.
- FakeLLMProvider does not represent real model behavior.
- No answer-level cost tracking in the original milestone (added later).
- No authorization or tenant scoping yet.

## Alternatives Considered

### Attach All Retrieved Candidates As Citations

The backend could always cite every retrieved chunk.

Rejected as the authoritative provenance path because that proves evidence
supply, not model-selected provenance. See ADR-023.

### Trust Model Citations Without Deterministic Validation

Rejected because models can invent citations or cite chunks incorrectly.

### Skip insufficient_context Handling

The system could always call the LLM even with no retrieved context.

Rejected because that encourages hallucination.

### Integrate a Real LLM Immediately

A real LLM provider could be added now.

Deferred originally to keep the initial implementation deterministic, cheap,
and focused on architecture. An optional OpenAI adapter was added later.

## Follow-Up

Related follow-up work includes:

- answer persistence
- answer trace records
- real LLM provider adapter
- deterministic provenance validation (ADR-023)
- LLM cost tracking
- semantic entailment / groundedness evaluation
- provider fallback strategy
