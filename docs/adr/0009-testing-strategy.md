# ADR-0009: Testing Strategy

## Status
Accepted

## Context
Formula errors are silent and must be caught early.

## Decision
Use three tiers: unit, integration, and end-to-end tests. Coverage targets: 90% computation modules, 70% overall.

## Consequences
- High confidence in deterministic outputs.
- Coverage is enforced in CI.
