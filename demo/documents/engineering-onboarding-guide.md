# Engineering Onboarding Guide

## Purpose

This guide helps new engineers become productive at Acme AI Platform.

The onboarding process focuses on local development, architecture understanding, code review habits, operational awareness, and customer empathy.

New engineers should learn how the platform is designed before making large implementation changes.

## First Week

During the first week, new engineers should set up the local development environment, run the test suite, read the architecture overview, review recent pull requests, and complete a small documentation or test improvement.

New engineers should also shadow one support escalation review and one incident review when available.

By the end of the first week, every new engineer should understand the repository structure, service boundaries, testing commands, and local Docker workflow.

## Development Environment

Engineers should run the application locally using Docker Compose when possible.

The local environment should include the API service, database, and any required local infrastructure services.

Secrets must not be committed to the repository.

External provider keys must be loaded through environment variables.

## Architecture Learning Path

New engineers should first read the README, architecture documents, and ADRs.

After that, they should trace one complete request through API routes, application services, domain entities, repositories, and infrastructure adapters.

Engineers working on AI features should understand the difference between ingestion, indexing, retrieval, answer generation, provider observability, and evaluation.

## Code Review Expectations

Code reviews should focus on correctness, maintainability, testing, failure modes, and operational impact.

Reviewers should ask whether the change is observable, whether errors are handled clearly, and whether the behavior is covered by tests.

Large unrelated changes should be split into smaller pull requests.

## Operational Awareness

New engineers should learn how to inspect logs, query traces, provider calls, usage reports, and evaluation results.

When investigating answer quality issues, engineers should inspect retrieval results before changing prompts.

When investigating cost issues, engineers should inspect provider call records and usage summaries.

## First Month Goals

By the end of the first month, new engineers should have shipped a small feature, improved tests or documentation, participated in a review, and explained one system design trade-off to the team.