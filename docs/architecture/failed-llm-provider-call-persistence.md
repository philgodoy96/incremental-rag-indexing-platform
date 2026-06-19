# Failed LLM Provider Call Persistence

## Purpose

Failed LLM Provider Call Persistence records LLM provider failures as durable provider call records.

Before this milestone, the platform persisted successful LLM provider calls during grounded answer generation.

This meant successful calls could be audited, but failed provider attempts were invisible unless they appeared in logs.

In production systems, this is not enough.

LLM providers are external dependencies. They can fail because of timeouts, rate limits, invalid responses, authentication issues, provider outages, networking failures, or unexpected SDK errors.

This makes those failures inspectable through the LLM Provider Call Read API.

## What Changed

The platform now supports failed provider call persistence when the LLM provider fails after retrieval returns context.

The service records a failed LLMProviderCallRecord with:

- status = failed
- answer_id = null
- query_trace_id populated
- provider populated
- model_name populated
- prompt_tokens = 0
- completion_tokens = 0
- total_tokens = 0
- estimated_cost_usd = 0
- latency_ms populated
- error_message populated

## Why answer_id Is Null

When the provider fails before answer generation completes, there is no successful AnswerRecord.

For that reason, failed provider calls are persisted with answer_id = null.

However, query_trace_id is still available because retrieval already completed before the provider call was attempted.

This preserves the audit chain back to retrieval even when no answer is produced.

## Provider Identity

To persist failures, the application needs provider identity before a successful response exists.

The LLMProvider interface now exposes:

- provider
- model_name

This allows the service to persist failed calls even if generate_answer raises an exception.

## Error Handling

The provider boundary now includes LLMProviderError.

Known provider failures should be raised as LLMProviderError.

Unexpected exceptions are caught, persisted as failed provider calls, and re-raised as LLMProviderError with a stable application-facing message.

This keeps the application boundary consistent while preserving the original failure context in persisted provider call records.

## Flow: Successful Call

    retrieval succeeds
    -> LLM provider succeeds
    -> AnswerRecord is created
    -> AnswerCitationRecord records are created
    -> LLMProviderCallRecord(status=succeeded, answer_id=answer.id) is created
    -> transaction commits

## Flow: Failed Call

    retrieval succeeds
    -> LLM provider fails
    -> LLMProviderCallRecord(status=failed, answer_id=null) is created
    -> transaction commits
    -> LLMProviderError is raised

## Flow: Insufficient Context

    retrieval returns no chunks
    -> no LLM provider call is attempted
    -> AnswerRecord(status=insufficient_context) is created
    -> no LLMProviderCallRecord is created

This is intentional.

If the LLM provider was never called, the system should not record provider activity.

## Read API Behavior

Failed calls are visible through:

    GET /api/v1/llm-provider-calls?status=failed

Failed calls can also be inspected by ID:

    GET /api/v1/llm-provider-calls/{provider_call_id}

Because failed calls have answer_id = null, they do not appear under:

    GET /api/v1/answers/{answer_id}/llm-provider-calls

## Audit Value

Failed call persistence helps engineers answer:

- Did retrieval succeed before the provider failed?
- Which provider/model failed?
- How long did the failed call take?
- What error was recorded?
- Are failures concentrated in one provider?
- Are timeouts increasing?
- Are errors happening before or after retrieval?
- Did a request fail without leaving an audit trail?

## Current Limitations

The current implementation uses zero token usage and zero cost for failed calls.

This is safe for now, but some real providers may return partial usage metadata even on failed or partially completed calls.

The current implementation does not yet support:

- provider-specific error categories
- retry attempt numbers
- fallback model tracking
- provider request IDs
- partial token usage on failed calls
- structured error codes
- failed answer records
- request-level correlation IDs in provider call records

## Future Work

Future improvements should include:

- structured provider error categories
- retry metadata
- fallback model metadata
- provider request IDs
- partial usage metadata when available
- timeout classification
- failed answer response modeling
- correlation with request_id and trace_id
- dashboard views for provider reliability at deployment time