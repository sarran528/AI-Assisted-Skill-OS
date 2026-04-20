# ADR-0012: Error Handling

## Status
Accepted

## Context
Failures must be consistent and safe for clients.

## Decision
FastAPI global exception handler returns structured JSON. LLM calls retry once, then return conservative defaults. Business failures return structured results, not 500s.

## Consequences
- Consistent client error handling.
- Reduced leakage of internal errors.
