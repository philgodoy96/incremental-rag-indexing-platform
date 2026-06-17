# LLM Provider Call Read API

## Purpose

The LLM Provider Call Read API exposes persisted LLM provider call records for inspection and auditability.

The platform already persists LLMProviderCallRecord during grounded answer generation.

This API makes those records accessible through application endpoints so engineers can inspect token usage, provider/model selection, estimated cost, latency, status, and answer/query trace links.

## Endpoints

### List LLM provider calls

GET /api/v1/llm-provider-calls

Supported query parameters:

- limit
- offset
- status
- provider
- model_name

Example request:

    GET /api/v1/llm-provider-calls?limit=20&offset=0&status=succeeded

Example response:

    {
      "items": [
        {
          "id": "uuid",
          "answer_id": "uuid",
          "query_trace_id": "uuid",
          "provider": "fake",
          "model_name": "fake-llm-v1",
          "status": "succeeded",
          "prompt_tokens": 10,
          "completion_tokens": 5,
          "total_tokens": 15,
          "estimated_cost_usd": "0.0001",
          "latency_ms": 125,
          "started_at": "2026-06-17T00:00:00Z",
          "completed_at": "2026-06-17T00:00:00.125000Z",
          "error_message": null,
          "created_at": "2026-06-17T00:00:00Z"
        }
      ],
      "limit": 20,
      "offset": 0
    }

### Get LLM provider call by ID

GET /api/v1/llm-provider-calls/{provider_call_id}

Returns one persisted provider call record.

If the provider call does not exist, the API returns 404.

### List LLM provider calls for an answer

GET /api/v1/answers/{answer_id}/llm-provider-calls

Returns provider calls linked to a specific persisted answer.

If the answer does not exist, the API returns 404.

## Why This API Matters

Persisting provider calls is useful, but not enough.

Engineers need API-level inspection to debug:

- expensive answers
- slow provider calls
- unexpected model usage
- token regressions
- failed provider calls
- answer-level cost attribution
- retrieval-to-generation behavior

This API turns provider observability into a usable debugging and audit workflow.

## Relationship to Answer Read API

The Answer Read API explains what answer was returned.

The LLM Provider Call Read API explains what LLM provider activity happened during answer generation.

Together, they allow the platform to answer:

- What did the system answer?
- Which retrieved chunks supported it?
- Which provider/model generated it?
- How many tokens were used?
- How much did it cost?
- How long did generation take?

## Audit Chain

The audit chain is:

    AnswerRecord
    -> LLMProviderCallRecord
    -> query_trace_id
    -> QueryTrace
    -> QueryTraceHit
    -> VectorIndexEntry
    -> ChunkVersion
    -> DocumentVersion

This enables answer-level debugging from final response back to retrieval and source data.

## API Design Notes

The top-level endpoint supports filtering by:

- status
- provider
- model_name

The nested answer endpoint validates parent answer existence before returning provider calls.

This avoids returning an empty list for an invalid answer_id, which could hide bugs in clients or admin tooling.

## Pagination

The current API uses limit and offset.

This is acceptable for early debugging and admin use.

For large production datasets, cursor pagination should replace offset pagination.

## Cost Serialization

estimated_cost_usd is returned as a string.

This avoids JSON float precision issues and preserves decimal semantics.

## Current Limitations

The API currently does not support:

- cursor pagination
- date range filters
- tenant/workspace scoping
- provider request IDs
- prompt version filters
- cost aggregation
- latency percentiles
- failed call exception categorization
- dashboard-ready metrics

## Future Work

Future improvements should include:

- cursor pagination
- started_at date filters
- tenant/workspace filters
- cost aggregation by provider/model
- answer-level total cost endpoint
- prompt version tracking
- provider request ID tracking
- failed call read/debug views
- dashboard metrics for cost and latency