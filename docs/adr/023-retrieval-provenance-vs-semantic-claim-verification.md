# ADR-023: Retrieval Provenance vs Semantic Claim Verification

## Status

Accepted

## Context

The grounded answer flow retrieves candidates, supplies them to an LLM, and must attach auditable citations to published answers.

An earlier design constructed citations from every retrieved candidate in backend code. That approach proved which evidence was *supplied* to generation, but it did not prove that the model selected a specific source or evidence span as provenance for its answer.

Separately, teams often conflate:

- retrieval evidence supplied to generation
- model-proposed provenance
- deterministically validated provenance
- semantic entailment / claim-level truth

The platform needs a clear, enforceable boundary for what citation validation proves.

## Decision

The generation contract requires the model to propose provenance:

- `answer`
- `citations[]` with a stable `candidate_id` from the immutable retrieval snapshot and a non-empty `evidence_span`

The application then validates proposed provenance deterministically before persistence:

1. The referenced candidate must exist in the exact retrieval snapshot used for that generation.
2. The evidence span must be non-empty after basic structural validation.
3. The evidence span must occur verbatim in the stored text of that candidate.
4. Candidates outside the snapshot are rejected even if the same chunk exists elsewhere.
5. Validation is performed by application code, never by an LLM judge.
6. Mixed valid and invalid proposed citations fail closed: no answer is published as provenance-validated. A completed provider invocation is still persisted for usage/cost observability with `answer_id=None`.

Persisted citation `quote` values are the validated evidence spans. Source/version identifiers remain those of the referenced retrieval candidates.

Deterministic provenance validation verifies that a model-selected evidence span came from a candidate in the immutable retrieval snapshot used for generation. It does not prove semantic entailment or factual correctness.

## Alternatives Considered

### Continue Backend-Owned Citations From All Retrieved Candidates

Rejected as the authoritative provenance path because it proves supply of evidence, not model-selected provenance.

### LLM-as-Judge / NLI Entailment Verification

Deferred. Semantic entailment is a different guarantee and would introduce non-deterministic or model-dependent claim checking.

### Fuzzy Semantic Matching as Authoritative Validator

Rejected. Fuzzy matching can accept spans that are not verbatim evidence and weakens auditability.

### Persist Answers With Invalid Provenance Flagged Softly

Rejected for this milestone. Fail-closed rejection is the minimum credible guarantee.

## Consequences

### Positive

- Published citations are model-proposed and application-validated.
- Stable candidate references (`chunk_version_id`) prevent text-only source matching.
- Documentation and APIs can claim a precise provenance guarantee without overclaiming correctness.
- Fake and real providers share the same structured contract and validation path.

### Negative

- Invalid model provenance causes answer publication to fail rather than silently falling back to all retrieved chunks.
- Rejected generations remain observable through LLMProviderCallRecord for usage and cost accounting.
- The answers API maps provenance-contract failures to HTTP 502 Bad Gateway.
- Verbatim span matching does not catch paraphrased but semantically supported claims.
- Empty or malformed model citation arrays fail closed even when retrieval succeeded.

## What Would Cause This Decision To Be Revisited

- Product requirements for claim-level groundedness or entailment checks
- Need for bounded repair / structured-output retry when provenance fails
- A requirement to publish answers with partial provenance under an explicit weaker status
- Introduction of offset-based evidence spans or richer citation schemas beyond verbatim text
