# Domain Model

## Purpose

This document describes the core domain entities of the Incremental RAG Indexing Platform.

Some sections describe implemented entities. Others describe planned concepts that are not yet persisted or exposed through APIs. See [Project Status](../project-status.md) for the current implemented capability list.

## Entity Groups

The system has seven major groups of domain concepts:

1. Source of truth entities
2. Derived artifacts
3. Projections
4. Operational data
5. Retrieval data
6. Evaluation data
7. User-facing data

## Source of Truth Entities

Source of truth entities represent durable facts the system must preserve.

### SourceDocument

Represents a logical document from a source system.

In V1, the source system is local Markdown files.

Important fields:

- id
- source_system
- external_id
- source_uri
- title
- current_document_version_id
- created_at
- updated_at
- deleted_at

Example values:

- source_system: local_seed_documents
- external_id: project-atlas-status.md
- source_uri: seed_documents/project-atlas-status.md

### DocumentVersion

Represents an immutable version of a source document.

Important fields:

- id
- source_document_id
- version_number
- content_checksum
- metadata_checksum
- raw_content
- created_at
- created_by_run_id

A DocumentVersion should never be updated after creation.

If the document changes, create a new DocumentVersion.

### SectionVersion

Represents an immutable section extracted from a DocumentVersion.

Important fields:

- id
- document_version_id
- stable_section_key
- heading_path
- heading_level
- title
- body
- section_checksum
- ordinal
- created_at

A SectionVersion should be deterministic for the same input document.

### ChunkVersion

Represents an immutable chunk created from a SectionVersion.

Important fields:

- id
- section_version_id
- chunk_index
- content
- heading_context
- chunk_hash
- embedding_input_hash
- token_estimate
- created_at
- risk_flags

A ChunkVersion is the citation target for grounded answers.

Answers should cite ChunkVersions, not entire documents.

## Derived Artifacts

Derived artifacts are produced from source of truth data.

They may be expensive to produce and should not be duplicated unnecessarily.

### EmbeddingRecord

Represents an embedding generated for a ChunkVersion.

Important fields:

- id
- chunk_version_id
- provider
- model
- dimension
- embedding_input_hash
- vector
- created_at

Identity should be based on:

    chunk_version_id + provider + model + dimension + embedding_input_hash

The system should not call an embedding provider twice for an already indexed embedding identity.

### EmbeddingCostRecord

Represents estimated cost for embedding operations.

Important fields:

- id
- provider
- model
- chunk_count
- token_count
- estimated_cost
- ingestion_run_id
- created_at

Cost records help explain operational cost over time.

## Projections

Projections are rebuildable views optimized for query performance.

### VectorIndexEntry

Represents a vector search entry.

Important fields:

- id
- embedding_record_id
- chunk_version_id
- vector
- indexed_at
- index_status

VectorIndexEntry can be rebuilt from EmbeddingRecord and current ChunkVersions.

It should not be treated as source of truth.

## Operational Data

Operational data explains system workflows and runtime decisions.

### IngestionRun

Represents one execution of ingestion.

Important fields:

- id
- source_system
- status
- started_at
- completed_at
- documents_seen
- documents_changed
- sections_created
- chunks_created
- embeddings_created
- estimated_cost
- error_message

### IngestionJob

Represents work related to a specific document or ingestion task.

Important fields:

- id
- ingestion_run_id
- source_document_id
- status
- attempt_count
- started_at
- completed_at
- error_message

V1 may execute ingestion synchronously.

Future versions may move jobs to workers.

### QueryTrace

Represents retrieval decision observability.

Important fields:

- id
- query
- search_type
- top_k
- filters
- retrieval_strategy
- candidate_count
- result_count
- duration_ms
- returned_chunk_ids
- scores
- created_at

QueryTrace explains retrieval behavior.

It is not a distributed trace.

### AuditLogEntry

Planned concept for dedicated audit-log persistence. Not implemented in the current repository.

Represents an important system event.

Important fields:

- id
- event_type
- entity_type
- entity_id
- metadata
- created_at

Examples of future event types:

- ingestion_started
- document_version_created
- chunk_version_created
- embedding_reused
- embedding_created
- retrieval_executed
- answer_generated
- prompt_injection_risk_detected

## Retrieval Data

### RetrievalResult

Represents one returned chunk from a search operation.

Important fields:

- chunk_version_id
- source_document_id
- document_version_id
- section_version_id
- score
- search_type
- rank
- metadata

This may be a domain object rather than a persisted entity.

## Evaluation Data

### EvaluationCase

Represents a test question and expected retrieval target.

Important fields:

- id
- dataset_version_id
- question
- expected_chunk_version_id
- expected_document_external_id
- expected_section_key
- notes

### EvaluationDatasetVersion

Represents an immutable evaluation dataset.

Important fields:

- id
- name
- version
- created_at
- description

### EvaluationRun

Represents one execution of retrieval evaluation.

Important fields:

- id
- dataset_version_id
- retrieval_strategy
- search_type
- top_k
- started_at
- completed_at
- hit_at_1
- hit_at_3
- hit_at_5
- mrr

### EvaluationResult

Represents one evaluation case result.

Important fields:

- id
- evaluation_run_id
- evaluation_case_id
- returned_chunk_ids
- expected_chunk_version_id
- rank_of_expected
- hit
- reciprocal_rank

## User-Facing Data

### GeneratedAnswer

Conceptual name for a persisted grounded answer. The implemented entity is `AnswerRecord`.

Important fields:

- id
- question
- answer_text
- status
- query_trace_id
- created_at

Implemented statuses:

- answered
- insufficient_context

`blocked_due_to_risk` is a planned future status and is not part of the current application flow.

### AnswerCitation

Conceptual name for a citation from an answer to a ChunkVersion. The implemented entity is `AnswerCitationRecord`.

Important fields:

- id
- generated_answer_id
- chunk_version_id
- quote
- citation_index

### AnswerFeedback

Planned concept for user feedback. Not implemented in the current repository.

Important fields:

- id
- generated_answer_id
- rating
- comment
- created_at

Feedback is not training data.

Feedback is operational evidence for future improvement.

## Important Invariants

1. DocumentVersion is immutable.
2. SectionVersion is immutable.
3. ChunkVersion is immutable.
4. Retrieval uses current versions unless explicitly evaluating history.
5. Answers cite ChunkVersions.
6. Embeddings are not regenerated when the same identity already exists.
7. VectorIndexEntry is rebuildable.
8. QueryTrace explains retrieval decisions.
9. Dedicated AuditLogEntry persistence is planned but not implemented in the current repository.
10. Retrieved documents are untrusted evidence, not instructions.