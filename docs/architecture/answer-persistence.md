# Answer Persistence

## Purpose

Answer persistence stores the final grounded answer returned by the system
after deterministic provenance validation succeeds.

Before this milestone, the platform persisted retrieval traces, but the final
answer only existed in the API response.

This document describes durable answer records so generated answers can be
audited after the request completes.

## Why This Matters

A production RAG platform needs to answer questions such as:

- What question was asked?
- What answer did the system return?
- Which query_trace_id supported the answer?
- Which validated provenance citations were returned?
- Which provider and model were used?
- Was the answer answered or insufficient_context?
- When was the answer created?

Without answer persistence, the platform can inspect retrieval behavior but
cannot inspect the final product delivered to the caller.

## Data Model

Answer persistence introduces two records:

- AnswerRecord
- AnswerCitationRecord

## AnswerRecord

AnswerRecord stores request-level and answer-level metadata.

It includes:

- id
- question
- answer
- status
- query_trace_id
- top_k
- provider
- model_name
- created_at

## AnswerCitationRecord

AnswerCitationRecord stores persisted validated provenance for an answer.

It includes:

- id
- answer_id
- rank
- vector_index_entry_id
- source_document_id
- document_version_id
- section_version_id
- chunk_version_id
- embedding_record_id
- stable_section_key
- chunk_index
- heading_context
- quote
- distance
- created_at

`quote` stores the validated evidence span proposed by the model and accepted
by deterministic provenance validation. It is not a dump of every retrieved
candidate and does not imply semantic entailment.

Source and version identifiers remain the immutable identities of the
referenced retrieval candidates.

## Provenance Persistence Rule

Only model-proposed citations that pass deterministic validation are
persisted.

Invalid provenance fails closed:

- the answer is not published as successfully provenance-validated
- citations are not silently replaced with all retrieved candidates
- no AnswerRecord or AnswerCitationRecord is persisted for the rejected draft
- the completed provider invocation is still persisted as an
  LLMProviderCallRecord with `answer_id=None` and status `succeeded`, so usage
  and cost accounting include rejected generations

Provenance rejection is an application rejection of otherwise completed provider
output. It is not a provider transport failure.

Deterministic provenance validation verifies that a model-selected evidence
span came from a candidate in the immutable retrieval snapshot used for
generation. It does not prove semantic entailment or factual correctness.

## Audit Chain

Answer persistence creates a durable audit chain:

    AnswerRecord
    -> query_trace_id
    -> QueryTrace
    -> QueryTraceHit
    -> ChunkVersion
    -> DocumentVersion

Validated citations also retain direct chunk/document version identifiers for
the accepted evidence spans.

This makes it possible to inspect both the answer and the retrieval execution
that supported it.

## Transaction Boundary

Answer persistence uses AnsweringTransaction.

AnsweringTransaction extends RetrievalTransaction with answer repositories.

This allows the answer service to use the same database transaction for:

- retrieval tracing
- answer persistence
- citation persistence

## API Behavior

The Grounded Answer API now returns answer_id.

Endpoint:

    POST /api/v1/answers

Response includes:

    {
      "answer_id": "uuid",
      "question": "What is Project Atlas status?",
      "answer": "Based on the retrieved context, Status: At Risk",
      "status": "answered",
      "query_trace_id": "uuid",
      "citations": []
    }

The answer_id can later be used to inspect the persisted answer.

## Current Limitations

Answer read APIs are available at:

- GET /api/v1/answers
- GET /api/v1/answers/{answer_id}

LLM provider calls, token usage metadata, estimated cost, and latency are
persisted through LLMProviderCallRecord and exposed through provider-call and
usage-reporting APIs.

The platform does not yet track:

- prompt template version
- semantic entailment / claim-level groundedness
- answer-level evaluation metrics
- tenant/workspace scoping

## Future Work

Future hardening may add:

- prompt version tracking
- answer trace records
- semantic entailment evaluation
- tenant/workspace scoping
- retention policies
