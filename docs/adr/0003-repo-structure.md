# ADR-0003: Repository Structure

## Status
Accepted

## Context
The system has shared contracts and a single deployment target.

## Decision
Use a monorepo with top-level folders: /backend, /frontend, /assessment, /rag, /infra, /tests.

## Consequences
- Shared contracts stay in sync.
- Single versioned deployment artifact.
