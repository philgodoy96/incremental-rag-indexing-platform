# ADR-007: Use Fake Deterministic Embeddings Before Real Providers

## Status

Accepted

## Context

The platform needs embedding records before it can support semantic retrieval.

However, integrating a real embedding provider too early would introduce:

- external API dependency
- API key requirements
- cost during tests
- nondeterministic operational failures
- provider-specific complexity before core indexing behavior is stable

The project needs to prove the indexing and persistence model before integrating OpenAI, Bedrock, or another provider.

## Decision

The system will introduce a fake deterministic embedding provider first.

The fake provider produces stable vectors from input text using a deterministic hashing strategy.

EmbeddingRecord and EmbeddingCostRecord will be modeled as production concepts even though the provider is fake.

The fake provider will have:

- provider: `fake`
- model_name: `fake-embedding-v1`
- fixed dimensions
- deterministic output
- zero estimated cost

## Alternatives Considered

### Call a Real Provider Immediately

This would be closer to production behavior.

Rejected for this slice because it would make tests and local development depend on external services and real costs.

### Skip Embedding Records Until Search

This would reduce implementation work.

Rejected because semantic search should depend on persisted embedding records, not generate embeddings implicitly during retrieval.

### Store Only Vectors Without Metadata

This would be simpler.

Rejected because provider, model, input hash, token estimate, and cost data are essential for auditability, re-indexing, and cost tracking.

## Consequences

### Positive

- Tests are deterministic.
- Local development has no external cost.
- Embedding persistence can be validated early.
- Re-embedding rules become explicit.
- Cost tracking shape exists before real providers.
- Future provider adapters can plug into the same interface.

### Negative

- Fake vectors are not semantically meaningful.
- Retrieval quality cannot be evaluated yet.
- Real provider behavior may require additional validation.
- Token estimates are still approximate.

## Follow-Up

Future work should introduce:

- real embedding provider adapters
- provider-specific pricing
- provider-specific dimensions
- pgvector storage
- vector index entries
- semantic retrieval endpoint