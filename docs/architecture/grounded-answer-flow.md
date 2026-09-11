# Grounded Answer Flow

## Purpose

The Grounded Answer API turns semantic retrieval results into an answer with
deterministically validated provenance citations.

This is the API path where the platform behaves like a RAG system from an API
consumer perspective.

The flow is:

1. Receive a user question.
2. Run semantic retrieval and retain an immutable retrieval snapshot.
3. Persist a query trace.
4. Ask the LLM for an answer draft plus proposed provenance citations.
5. Validate proposed provenance deterministically against the retrieval snapshot.
6. Persist and return only validated provenance with the answer.

## Provenance Terminology

Keep these layers distinct:

- **Retrieval evidence supplied to generation**: candidates present in the
  immutable retrieval snapshot passed to the model.
- **Model-proposed provenance**: candidate references and evidence spans
  returned by the model. The model may propose provenance; it may not
  establish it.
- **Deterministically validated provenance**: proposed citations that passed
  application validation and were persisted/published.
- **Semantic entailment**: whether an answer claim is logically supported by
  evidence. Not implemented by this flow.

Deterministic provenance validation verifies that a model-selected evidence
span came from a candidate in the immutable retrieval snapshot used for
generation. It does not prove semantic entailment or factual correctness.

## API Endpoint

POST /api/v1/answers

Example request:

    {
      "question": "What is Project Atlas status?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Example answered response:

    {
      "question": "What is Project Atlas status?",
      "answer": "Based on the retrieved context, Status: At Risk",
      "status": "answered",
      "query_trace_id": "uuid",
      "citations": [
        {
          "rank": 1,
          "vector_index_entry_id": "uuid",
          "source_document_id": "uuid",
          "document_version_id": "uuid",
          "section_version_id": "uuid",
          "chunk_version_id": "uuid",
          "embedding_record_id": "uuid",
          "stable_section_key": "project-atlas-status/summary",
          "chunk_index": 0,
          "heading_context": ["Project Atlas Status", "Summary"],
          "quote": "Status: At Risk",
          "distance": 0.12
        }
      ]
    }

In answered responses, `quote` is the validated evidence span, not necessarily
the full retrieved chunk text.

Example insufficient context response:

    {
      "question": "What is Project Phoenix budget?",
      "answer": "I do not have enough retrieved context to answer this question reliably.",
      "status": "insufficient_context",
      "query_trace_id": "uuid",
      "citations": []
    }

Invalid model-proposed provenance fails closed. The API returns HTTP 502 Bad
Gateway because a valid client request reached a provider-contract failure: the
LLM call completed, but the application rejected the generated provenance.
No answer or citations are persisted as provenance-validated. The completed
provider invocation is still recorded for usage and cost observability with
`answer_id=None` and status `succeeded`.

## Architecture

The GroundedAnswerService orchestrates the answer flow.

It depends on:

- SemanticRetriever
- LLMProvider
- ProvenanceValidator
- AnsweringTransaction / RetrievalTransaction

The SemanticRetriever performs retrieval and returns retrieved chunks plus
query_trace_id.

Each context chunk supplied to the LLM includes a stable opaque
`candidate_id` (`chunk_version_id` string) from the retrieval snapshot.

The LLMProvider returns structured output:

- answer text
- proposed citations (`candidate_id`, `evidence_span`)

ProvenanceValidator validates proposed citations against the exact retrieval
snapshot used for that generation.

Only validated citations are persisted and returned.

## Deterministic Validation Rules

For every proposed citation:

1. The referenced candidate must exist in the exact retrieval snapshot.
2. The evidence span must be non-empty after basic structural validation.
3. The evidence span must occur verbatim in that candidate's stored text.
4. A candidate outside the snapshot is rejected even if the same chunk exists
   elsewhere in the database.
5. Validation is application code, not an LLM judge.
6. Mixed valid and invalid citations fail the whole provenance validation.

## Why The Model Proposes And The Application Establishes Provenance

Prompt instructions ask the model to cite supplied candidates with verbatim
spans. Those instructions are behavioral guidance only.

The application validator is authoritative. Fake and real providers both emit
the same structured contract and both pass through the same validator.

## Current Provider Strategy

The default implementation uses FakeLLMProvider.

FakeLLMProvider is deterministic and local. It proposes a citation by copying
a literal evidence span from a supplied candidate, then the application
validator still executes.

A real provider such as OpenAI returns the same structured answer + citations
contract behind the LLMProvider boundary.

## GroundedAnswerStatus

The answer status can be:

- answered
- insufficient_context

answered means retrieval returned context, the model returned an answer draft,
and proposed provenance passed deterministic validation.

insufficient_context means retrieval returned no chunks, so the system refused
to invent an answer.

## Query Trace Integration

Every answer response includes query_trace_id.

This allows engineers to inspect the retrieval execution that supported the
answer.

The query trace can be read using:

- GET /api/v1/retrieval/traces/{trace_id}

This makes the retrieval side of the answer auditable. Validated citations
separately record which model-proposed evidence spans were accepted.

## Current Limitations

The current implementation:

- persists answer records
- links answers to query traces and provider call records
- validates provenance deterministically before persistence
- uses fake LLM provider by default and optional OpenAI LLM provider

It does not yet:

- verify semantic entailment or claim-level factual correctness
- stream responses
- support multi-turn conversations
- apply tenant/workspace filters
- enforce authorization
- redact sensitive retrieved content

## Future Work

Future hardening may add:

- semantic entailment / groundedness evaluation
- bounded structured-output repair on provenance failure
- additional LLM provider adapters
- refusal policy improvements
- tenant/workspace scoping
