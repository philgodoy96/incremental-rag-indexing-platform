# Initial Seed Documents

## Purpose

This document explains the first seed documents committed to the repository.

Seed documents are part of the system design and testing strategy.

They are not placeholder content.

## Documents Introduced

### project-atlas-status.md

Purpose:

- tests project status retrieval
- provides changing status fields
- introduces ownership and risk information
- supports future incremental indexing scenarios

Future evolution scenarios:

- change status from `at risk` to `on track`
- add a new security review section
- update the production-readiness review date
- change the owning team for retrieval evaluation

### redis-queue-backlog-runbook.md

Purpose:

- tests operational runbook retrieval
- provides concrete incident response steps
- includes idempotency-related content
- supports future grounded answer citations

Future evolution scenarios:

- change the escalation threshold from 15 minutes to 10 minutes
- rename `Initial Triage` to `First Response`
- add a new mitigation step for poison-pill jobs
- update retry safety guidance

### adr-001-pgvector-retrieval-architecture.md

Purpose:

- tests retrieval over architecture decisions
- provides trade-offs and alternatives
- explains why pgvector is used in V1
- supports future citation tests for ADR-style content

Future evolution scenarios:

- add limitations around index size
- add an alternative for managed vector databases
- update the rebuildability strategy
- add notes about future hybrid retrieval hardening

## Why These Documents Come First

These documents cover three important enterprise knowledge types:

1. project status
2. operational runbooks
3. architecture decisions

Together they allow the platform to test different retrieval behaviors across project status, operational runbook, and architecture-decision content.