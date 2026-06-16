# Project Atlas Status

## Summary

Project Atlas is an internal initiative to improve retrieval quality for engineering knowledge across platform teams.

The current delivery status is `at risk` because the retrieval evaluation dataset is not yet complete.

The target production-readiness review date is 2026-07-15.

## Current Milestones

### M1: Incremental Indexing Foundation

Status: in progress.

The indexing foundation must detect changed documents without reprocessing unchanged content.

The first implementation uses local Markdown documents as the source system.

### M2: Retrieval Evaluation

Status: not started.

The evaluation milestone must define golden questions, expected evidence chunks, and baseline retrieval metrics.

### M3: Grounded Answer Generation

Status: blocked.

Grounded answer generation depends on retrieval returning reliable ChunkVersion evidence with citation metadata.

## Risks

### Evaluation Dataset Delay

The biggest risk is that evaluation cases may be created too late.

Without evaluation cases, retrieval changes cannot be validated objectively.

### Cost Visibility Gap

The platform must estimate embedding cost before indexing large batches.

Cost tracking is required before real embedding providers are enabled.

## Ownership

The platform engineering team owns ingestion and indexing.

The applied AI team owns retrieval quality and evaluation design.

The security team owns prompt injection review.