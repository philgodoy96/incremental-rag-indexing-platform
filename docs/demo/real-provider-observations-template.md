# Real Provider Observations Template

## Purpose

Use this template to record observations after running a controlled real provider demo.

Do not include secrets.

## Run Metadata

- Date:
- Environment:
- Provider:
- Model:
- Retrieval provider:
- Retrieval model:
- Question:

## Answer Quality

- Was the answer grounded in retrieved context?
- Did the answer avoid unsupported claims?
- Was the answer clear and useful?
- Were citations present?
- Were citations relevant?

## Observability

- Answer ID:
- Query trace ID:
- Provider call ID:
- Provider call status:
- Latency milliseconds:
- Prompt tokens:
- Completion tokens:
- Total tokens:
- Estimated cost USD:

## Retrieval Quality

- Did retrieval return the expected document?
- Did retrieval return the expected section/chunk?
- Was top_k sufficient?
- Would evaluation metrics catch a regression for this query?

## Failure Notes

- Did any provider error occur?
- Did any timeout occur?
- Did usage metadata appear?
- Did cost reporting update correctly?

## Follow-Up Decisions

- Should model configuration change?
- Should max output tokens change?
- Should prompt/instructions change?
- Should retrieval strategy change?
- Should evaluation cases be updated?