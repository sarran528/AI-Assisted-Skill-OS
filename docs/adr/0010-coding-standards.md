# ADR-0010: Coding Standards

## Status
Accepted

## Context
Consistent formatting and typing are required.

## Decision
Python uses ruff, black, mypy. TypeScript uses eslint and prettier. All functions are typed; no any in TS. Docstrings required on public computation functions. Formula constants are named and centralized.

## Consequences
- Style and type issues are caught early.
- Formula logic is reviewable.
