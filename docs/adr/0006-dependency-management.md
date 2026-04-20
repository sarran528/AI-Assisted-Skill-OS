# ADR-0006: Dependency Management

## Status
Accepted

## Context
Deterministic behavior requires fixed dependencies.

## Decision
Python dependencies pinned with == in requirements.txt. Node uses npm with package-lock.json committed.

## Consequences
- Builds are reproducible.
- Dependency upgrades are intentional.
