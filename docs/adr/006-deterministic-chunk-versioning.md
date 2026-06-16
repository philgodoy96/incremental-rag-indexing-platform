# ADR-006: Use Deterministic Chunk Versioning

## Status

Accepted

## Context

The platform needs retrieval units smaller than sections.

Chunks will later be used for:

- embeddings
- vector search
- hybrid retrieval
- grounded answer citations
- evaluation expected evidence

If chunking is nondeterministic, indexing becomes difficult to debug and evaluate.

## Decision

The system will create immutable ChunkVersion records from SectionVersion records.

Chunking will be deterministic and based on:

- section body
- heading context
- target chunk word count
- overlap word count

Each ChunkVersion stores:

- chunk content
- heading context
- chunk hash
- embedding input hash
- token estimate

## Alternatives Considered

### Embed Whole Sections

This is simpler, but long sections may exceed ideal embedding input size and reduce retrieval precision.

Rejected because chunk-level retrieval is needed for grounded answers and future citation quality.

### Use Provider-Specific Tokenizers First

This would be more accurate for token counting.

Rejected for V1 because it would introduce provider coupling before the fake embedding provider exists.

The current implementation uses word-based estimates and can evolve later.

### Nondeterministic or LLM-Based Chunking

LLM-based chunking could create more semantic chunks.

Rejected for V1 because it is harder to reproduce, test, and reason about.

## Consequences

### Positive

- Predictable indexing behavior
- Easier testing
- Easier evaluation reproducibility
- Clear input for embedding generation
- Future cost estimation becomes possible

### Negative

- Word-based chunking is approximate
- Semantic boundaries may be imperfect
- Provider-specific token limits are not handled yet
- Chunking configuration changes require careful evaluation

## Follow-Up

Future improvements may include:

- tokenizer-aware chunking
- semantic boundary detection
- experiment documents for chunk size changes
- evaluation comparisons between chunk configurations