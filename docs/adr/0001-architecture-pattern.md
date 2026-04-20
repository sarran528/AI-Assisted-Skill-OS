# ADR-0001: Architecture Pattern

## Status
Accepted

## Context
The system is defined with strict layers and a single orchestration authority.

## Decision
Use a modular monolith with enforced boundaries.

## Consequences
- Clear layer ownership without microservice overhead.
- Easier deployment and shared contracts.
