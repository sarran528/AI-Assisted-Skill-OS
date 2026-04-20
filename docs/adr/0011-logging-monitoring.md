# ADR-0011: Logging and Monitoring

## Status
Accepted

## Context
Operational visibility is required across services.

## Decision
Structured JSON logs with required fields and Prometheus metrics at /metrics.

## Consequences
- Logs are machine searchable.
- Metrics support alerting.
