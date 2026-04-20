# ADR-0014: API Design Style

## Status
Accepted

## Context
API behavior must be consistent and versioned.

## Decision
REST with /api/v1 prefix. Plural resource names. snake_case JSON fields. Correct HTTP status usage.

## Consequences
- Stable versioning from day one.
- Predictable client behavior.
