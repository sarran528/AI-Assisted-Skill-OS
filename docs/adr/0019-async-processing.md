# ADR-0019: Async Processing

## Status
Accepted

## Context
LLM work and long-running jobs must be handled asynchronously with predictable retries and timeouts.

## Decision
Use Celery with Redis as the broker and PostgreSQL as the result backend.

## Consequences
- Job execution is decoupled from API request latency.
- Redis and Postgres are required in all environments.
