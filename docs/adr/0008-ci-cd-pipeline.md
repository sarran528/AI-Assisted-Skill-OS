# ADR-0008: CI/CD Pipeline

## Status
Accepted

## Context
Quality gates must run before deployments.

## Decision
GitHub Actions pipeline: lint -> type check -> unit tests -> integration tests -> build -> push -> deploy to staging. Production deploy requires manual approval.

## Consequences
- No deploy if tests fail.
- Traceable, staged releases.
