# ADR-0015: Performance Constraints

## Status
Accepted

## Context
Define baseline performance expectations.

## Decision
Synchronous API responses under 500ms. LLM jobs async with up to 30s latency. Index on user_id and profile_id.

## Consequences
- Clear baseline for tuning.
- Supports async job patterns.
