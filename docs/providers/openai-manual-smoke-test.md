# OpenAI Manual Smoke Test

## Purpose

This guide explains how to manually validate the optional OpenAI LLM provider integration.

The smoke test is intentionally manual.

Automated tests must not call OpenAI or require a real API key.

## Safety Rules

Before running the smoke test:

- confirm `.env` is ignored by Git
- confirm no API key is staged
- use a low-cost model
- keep max output tokens bounded
- run only a small number of requests
- inspect provider calls and usage reporting after the test
- switch back to the fake provider after the test

## Preflight Checks

Run:

    git status --ignored

Expected behavior:

- `.env` appears only as ignored
- `.env` does not appear as untracked
- `.env` does not appear as staged

Run:

    Select-String -Path .gitignore -Pattern "^\.env$|\.env"

Expected behavior:

- `.env` is ignored
- `.env.example` remains allowed

## Local Environment

Create or update your local `.env` file.

Example:

    LLM_PROVIDER=openai
    OPENAI_API_KEY=replace-with-local-secret
    OPENAI_MODEL=gpt-5.4-mini
    OPENAI_TIMEOUT_SECONDS=30
    OPENAI_MAX_OUTPUT_TOKENS=800
    OPENAI_INPUT_PRICE_PER_1M_TOKENS_USD=0.75
    OPENAI_OUTPUT_PRICE_PER_1M_TOKENS_USD=4.50

Do not commit `.env`.

## Start the Application

Start the local environment using the project setup instructions.

Typical flow:

    docker compose up --build

Or, if running locally without Docker:

    uvicorn app.main:create_app --factory --reload

Adjust the command based on the actual project setup.

## Provider Selection

The answer API request selects retrieval provider/model through:

- provider
- model_name

The LLM provider is selected through runtime configuration:

    LLM_PROVIDER=openai

The answer request body should not include `llm_provider`, `llm_model_name`, `retrieval_provider`, or `retrieval_model_name`.

## Recommended Smoke Test Question

Use a question that should be answerable from the demo dataset:

    Who owns Project Atlas?

Expected answer:

- identifies Platform Intelligence team
- mentions Maya Chen as accountable engineering manager
- mentions Jordan Lee as product lead if enough context was retrieved
- includes citations when retrieval returns context
- does not invent unsupported details

## Generate Grounded Answer

Request shape:

    POST /api/v1/answers

Example payload:

    {
      "question": "Who owns Project Atlas?",
      "top_k": 5,
      "provider": "fake",
      "model_name": "fake-embedding-v1"
    }

Notes:

- retrieval can still use the fake embedding provider
- answer generation uses OpenAI when `LLM_PROVIDER=openai`
- if retrieval returns no chunks, the answer flow may return insufficient context instead of calling the LLM

## Inspect Answer

After generating the answer, inspect persisted answers:

    GET /api/v1/answers
    GET /api/v1/answers/{answer_id}

Check:

- answer was persisted
- citations were persisted when context was available
- answer is grounded in retrieved chunks

## Inspect Provider Call

Inspect LLM provider calls:

    GET /api/v1/llm-provider-calls
    GET /api/v1/llm-provider-calls/{provider_call_id}

Check:

- provider is `openai`
- model name matches configured model
- status is `succeeded`
- latency is recorded
- token usage is recorded when available
- estimated cost is recorded when available

## Inspect Usage Reporting

Inspect aggregate usage:

    GET /api/v1/llm-usage/summary
    GET /api/v1/llm-usage/by-model

Check:

- call_count increased
- succeeded_count increased
- total_tokens increased when usage metadata is available
- estimated_cost_usd increased when usage metadata is available
- by-model reporting includes OpenAI model entry

## Failure Smoke Tests

These should be run carefully and only when useful.

### Missing API Key

Set:

    LLM_PROVIDER=openai
    OPENAI_API_KEY=

Expected behavior:

- application or provider initialization fails clearly
- error mentions that OPENAI_API_KEY is required

### Invalid API Key

Set an invalid API key.

Expected behavior:

- provider call fails
- failure is mapped to internal provider error
- failed provider call is persisted if failure happens during answer generation flow
- failed call can be inspected through provider call read API

### Timeout

Set a very small timeout:

    OPENAI_TIMEOUT_SECONDS=0.001

Expected behavior:

- request times out
- failure is mapped clearly
- failed provider call is persisted if the failure happens during answer generation flow

## After the Smoke Test

Switch back to fake provider:

    LLM_PROVIDER=fake

Restart the application.

Run:

    pytest
    ruff check .
    mypy app tests

Automated checks should not depend on OpenAI.

## Observations To Record

Record observations in a separate demo observations document after running the real provider flow.

Useful fields:

- date
- model
- prompt/question
- answer quality
- citation quality
- latency
- prompt tokens
- completion tokens
- total tokens
- estimated cost
- provider call status
- any failures
- notes or follow-up decisions

## Important Notes

Model availability and pricing can change.

Keep model name and pricing configurable through environment variables.

Do not hardcode a pricing assumption permanently in business logic.

Do not treat a single successful smoke test as production readiness.