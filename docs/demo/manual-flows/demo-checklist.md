# Demo Checklist

Use this checklist before presenting the project.

## Environment

- [ ] Application starts locally.
- [ ] Database is running.
- [ ] Migrations are applied.
- [ ] API health endpoint responds.
- [ ] Swagger or API docs are accessible.
- [ ] Fake providers are enabled by default.
- [ ] No external API key is required.

## Dataset

- [ ] `python scripts/preview_demo_dataset.py` works.
- [ ] Dataset name is `acme_internal_knowledge_demo`.
- [ ] Dataset version is `1.0.0`.
- [ ] Four demo documents are listed.
- [ ] Each document has a checksum.
- [ ] Manifest paths resolve correctly.

## Indexing

- [ ] Demo documents are loaded.
- [ ] Document versions exist.
- [ ] Sections or chunks exist.
- [ ] Embeddings exist.
- [ ] Vector index entries exist.

## Retrieval

- [ ] `What is Project Atlas?` retrieves Project Atlas content.
- [ ] `Who owns Project Atlas?` retrieves ownership content.
- [ ] `What should support do before escalating a customer issue?` retrieves escalation policy content.
- [ ] `What is the incident severity process?` retrieves incident response content.
- [ ] `What should new engineers do in their first week?` retrieves onboarding content.

## Query Tracing

- [ ] Query trace is created after retrieval.
- [ ] Query trace lists retrieval hits.
- [ ] Query trace includes provider/model metadata.
- [ ] Query trace can be read through the API.

## Grounded Answers

- [ ] Answer generation returns an answer.
- [ ] Answer includes citations.
- [ ] Answer is persisted.
- [ ] Citations are persisted.
- [ ] Answer can be read after generation.

## Provider Observability

- [ ] LLM provider call record is created.
- [ ] Provider/model are recorded.
- [ ] Status is recorded.
- [ ] Usage metadata is recorded when available.
- [ ] Failed calls can be inspected when simulated.

## Usage Reporting

- [ ] Usage summary returns call_count.
- [ ] Usage summary returns succeeded_count.
- [ ] Usage summary returns failed_count.
- [ ] Usage summary returns token totals when available.
- [ ] Usage by model groups calls by provider/model.

## Retrieval Evaluation

- [ ] Evaluation cases exist.
- [ ] Evaluation run executes.
- [ ] Case results are persisted.
- [ ] Summary includes hit_rate_at_k.
- [ ] Summary includes mean_recall_at_k.
- [ ] Summary includes mean_reciprocal_rank.

## Portfolio Readiness

- [ ] Demo can be explained in under five minutes.
- [ ] README points to demo docs.
- [ ] Architecture docs explain the major components.
- [ ] ADRs explain important decisions.
- [ ] Tests pass.
- [ ] No secrets are committed.