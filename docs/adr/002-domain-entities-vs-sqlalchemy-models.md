# ADR-002: Separate Domain Entities from SQLAlchemy Models

## Status

Accepted

## Context

The platform contains domain concepts that are more important than database tables.

Examples:

- SourceDocument
- DocumentVersion
- SectionVersion
- ChunkVersion
- EmbeddingRecord
- QueryTrace
- EvaluationRun
- GeneratedAnswer
- AnswerCitation

A simple implementation could use SQLAlchemy models directly inside application services.

That would be faster, but it would couple business rules to persistence details.

The system needs domain behavior that can be tested and reasoned about without requiring a database session.

## Decision

The system will separate domain entities from SQLAlchemy models.

Application services will depend on domain entities and repository interfaces.

Infrastructure repositories will map between SQLAlchemy models and domain entities.

Application services should not directly manipulate SQLAlchemy models.

## Example Boundary

Application service:

    IngestionService

Should work with:

    SourceDocument
    DocumentVersion
    SectionVersion
    ChunkVersion

It should not directly depend on:

    SourceDocumentModel
    DocumentVersionModel
    SectionVersionModel
    ChunkVersionModel

Mapping happens in the infrastructure layer.

## Alternatives Considered

### Use SQLAlchemy Models as Domain Objects

This is common in smaller applications.

It reduces boilerplate and speeds up development.

Rejected because this project needs:

- clearer domain boundaries
- easier unit testing
- infrastructure replaceability
- explicit mapping
- better architecture discipline

### Use a Full DDD Framework

A full DDD framework would add patterns such as aggregates, domain events, repositories, specifications, and unit of work abstractions.

Rejected for now because the system should remain understandable and practical.

The system will use DDD-inspired separation without unnecessary ceremony.

## Consequences

### Positive

- Domain logic is easier to test
- Application services are less coupled to SQLAlchemy
- Persistence can evolve independently
- Domain concepts are clearer
- The architecture is easier to explain and review

### Negative

- More mapping code
- More files
- Slower initial implementation
- Possible duplication between domain fields and database columns

## Engineering Rule

If a business invariant belongs to the domain, it should not be hidden only inside the database model.

If a field exists only for persistence mechanics, it may belong only to the database model.

## Examples

Domain-level concern:

    A ChunkVersion must be immutable after creation.

Persistence-level concern:

    The chunk_versions table has an index on section_version_id.

Both matter, but they belong in different layers.

## Review Question

When adding new functionality, ask:

    Is this a domain rule, an application workflow, or a persistence detail?

The answer determines where the code should live.