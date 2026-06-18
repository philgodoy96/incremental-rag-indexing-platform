# OpenAI Provider Setup

## Purpose

This document explains how to enable OpenAI as an optional LLM provider.

The project uses fake providers by default.

OpenAI is intended for controlled local demos and manual validation.

Automated tests must not call OpenAI.

## Default Behavior

The default provider is:

    LLM_PROVIDER=fake

This means the project can run without external API keys.

## Enable OpenAI Locally

Create a local `.env` file that is not committed to Git.

Example:

    LLM_PROVIDER=openai
    OPENAI_API_KEY=replace-with-your-local-key
    OPENAI_MODEL=gpt-5.4-mini
    OPENAI_TIMEOUT_SECONDS=30
    OPENAI_MAX_OUTPUT_TOKENS=800
    OPENAI_INPUT_PRICE_PER_1M_TOKENS_USD=0.75
    OPENAI_OUTPUT_PRICE_PER_1M_TOKENS_USD=4.50

Never commit `.env`.

Use `.env.example` for documenting variable names only.

## Safety Rules

- Do not commit API keys.
- Do not paste API keys in issues, pull requests, docs, or chat.
- Do not run automated tests against real OpenAI.
- Keep fake provider as the default.
- Enable OpenAI only through explicit local configuration.
- Use low-cost models for demos.
- Keep max output tokens bounded.
- Track usage through provider call records and usage reporting APIs.

## Expected Observability

When OpenAI is enabled, answer generation should still produce:

- persisted answers
- persisted citations
- provider call records
- usage metadata when available
- estimated cost when usage is available
- usage summaries by provider/model

## Failure Modes To Test Manually

- missing API key
- invalid API key
- provider timeout
- rate limit
- model not found
- unexpected provider response
- usage metadata unavailable

## Notes

Pricing and model availability can change.

Keep provider model and pricing configuration explicit so the project does not hardcode assumptions permanently.