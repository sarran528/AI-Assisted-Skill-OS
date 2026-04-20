# ADR-0004: Environment Strategy

## Status
Accepted

## Context
Multiple environments are required with consistent configuration.

## Decision
Use four environments (local, dev, staging, production). Configuration via environment variables only. Secrets live in a secrets manager, not in committed files.

## Consequences
- Repeatable deployments across environments.
- No secrets stored in version control.
