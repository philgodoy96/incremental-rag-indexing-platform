# Incident Response Playbook

## Purpose

This playbook defines how Acme AI Platform responds to production incidents.

An incident is any event that negatively impacts system availability, data integrity, security, customer operations, or critical internal workflows.

The goal of incident response is to restore service safely, communicate clearly, and learn from failures.

## Severity Levels

SEV1 incidents are critical incidents.

A SEV1 means the production system is unavailable, customer data integrity is at risk, or a security-sensitive failure is active.

SEV2 incidents are major incidents.

A SEV2 means a major feature is degraded, a subset of customers is impacted, or operational workarounds are required.

SEV3 incidents are minor incidents.

A SEV3 means impact is limited, internal-only, or recoverable without urgent customer communication.

## Incident Roles

Every SEV1 or SEV2 incident must have an incident commander.

The incident commander coordinates response, assigns owners, manages communication, and keeps the team focused.

The technical lead investigates the root technical issue.

The communications lead posts updates to internal stakeholders and customer-facing channels when required.

## Response Process

The first responder should confirm impact, assign severity, and open an incident channel.

The incident commander should be assigned as soon as possible for SEV1 and SEV2 incidents.

The team should stabilize the system before performing risky root-cause experiments.

Mitigation is prioritized over perfect diagnosis during active customer impact.

## Communication

For SEV1 incidents, internal updates should be posted every fifteen minutes until the incident is mitigated.

For SEV2 incidents, internal updates should be posted every thirty minutes.

Customer-facing updates must be accurate, concise, and avoid speculative root cause claims.

## Post-Incident Review

Every SEV1 incident requires a written post-incident review.

The review should include timeline, impact, root cause, contributing factors, remediation items, owners, and due dates.

The review should focus on system improvement instead of blame.

## Completion Criteria

An incident is considered resolved when customer impact has ended, monitoring confirms recovery, and the incident commander has closed the active response.

Follow-up work remains tracked separately after resolution.