# ADR-0007: Build and Run System

## Status
Accepted

## Context
Local setup must be uniform and predictable.

## Decision
Use Docker for all services and docker-compose for local development. Provide a single Makefile entry point.

## Consequences
- New developers can start with one command.
- Runtime parity between local and production.
