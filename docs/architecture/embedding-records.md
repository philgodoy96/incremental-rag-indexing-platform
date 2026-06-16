# Embedding Records

## Purpose

Embedding records persist the vector representation generated from ChunkVersion records.

This layer separates retrieval-ready text chunks from provider-specific embedding outputs.

The system should not call an embedding provider repeatedly for the same semantic input, provider, and model combination.

## Current Flow

During local seed ingestion:

1. Markdown documents are discovered.
2. SourceDocument and DocumentVersion records are created or reused.
3. SectionVersion records are created or reused.
4. ChunkVersion records are created or reused.
5. EmbeddingRecord records are created for chunks that do not already have an embedding for the configured provider, model, and embedding input hash.
6. EmbeddingCostRecord records are created for new embeddings.
7. IngestionRun stores embedding creation and cost summary fields.

## EmbeddingRecord Fields

An EmbeddingRecord includes:

- chunk_version_id
- provider
- model_name
- embedding_input_hash
- embedding_vector
- dimensions
- input_token_estimate
- created_at

## Embedding Input Hash

The embedding input hash represents the exact semantic input used to generate the embedding.

It is not just the chunk content hash.

A chunk stores original retrievable content.

The embedding input may include additional context such as:

- heading context
- section title
- document title
- future metadata
- future risk flags

This allows the system to detect whether the embedding input changed without confusing it with raw chunk content changes.

## Chunk Hash vs Embedding Input Hash

chunk_hash answers:

    Did the chunk content change?

embedding_input_hash answers:

    Did the text sent to the embedding provider change?

These are different because embedding input can include heading context around the chunk.

## Fake Embedding Provider

The current implementation uses a deterministic fake embedding provider.

The fake provider:

- has provider name `fake`
- has model name `fake-embedding-v1`
- returns fixed-size vectors
- produces the same vector for the same input
- has estimated cost zero

This allows local development and tests without external API calls or API keys.

## Embedding Cost Records

EmbeddingCostRecord stores the cost attribution for each newly generated embedding.

For fake embeddings, the estimated cost is zero.

The cost record still exists because the system needs the same accounting shape before real providers are introduced.

## Idempotency

Embeddings are not regenerated when an EmbeddingRecord already exists for:

- chunk_version_id
- provider
- model_name
- embedding_input_hash

This prevents duplicate provider calls and duplicate cost records for unchanged chunks.

## Current Limitations

This slice does not yet support:

- pgvector storage
- vector index entries
- semantic search
- embedding provider fallback
- async embedding jobs
- retry/backoff handling
- provider rate limiting
- real token counting
- real provider pricing

## Follow-Up Work

Future slices should introduce:

- VectorIndexEntry
- pgvector column storage
- semantic search endpoint
- retrieval traces
- real embedding provider adapters
- provider-specific cost estimation
- async embedding jobs