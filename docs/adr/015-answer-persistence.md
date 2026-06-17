# ADR-015: Persist Grounded Answers

## Status

Accepted

## Context

The platform supports semantic retrieval, query tracing, trace reading, and grounded answer generation.

However, grounded answers were not persisted.

This means the API caller could receive an answer, but the platform could not later inspect the exact final answer that was delivered.

For a production RAG platform, answer persistence is required for auditability, debugging, evaluation, and future product workflows.

## Decision

The system will persist grounded answers using:

- AnswerRecord
- AnswerCitationRecord

AnswerRecord stores the final answer and request metadata.

AnswerCitationRecord stores the citations returned with that answer.

The Grounded Answer API will return answer_id.

## Consequences

### Positive

- Answers become auditable after request completion.
- API consumers receive answer_id for future inspection.
- Citations are durably linked to the answer.
- Answers can be connected to retrieval traces through query_trace_id.
- The platform is prepared for answer evaluation and admin tooling.

### Negative

- Adds additional database writes to answer generation.
- Increases storage usage.
- Stores user questions, generated answers, and citation quotes.
- Requires future retention and privacy policies.
- Answer read APIs are still needed.

## Alternatives Considered

### Do Not Persist Answers

The system could rely only on API responses and query traces.

Rejected because query traces explain retrieval, not the final answer delivered to the caller.

### Store Answer and Citations in One JSON Column

The system could store citations inside AnswerRecord as JSON.

Rejected because citations are useful as queryable domain records and may need filtering, ranking inspection, and analytics later.

### Persist Only Answer Text

The system could store only the final answer without citation records.

Rejected because citations are essential for auditability and groundedness workflows.

## Follow-Up

Future work should add:

- answer read endpoints
- answer list endpoint
- citation verification
- LLM cost tracking
- prompt version tracking
- provider latency tracking
- answer evaluation
- retention policies