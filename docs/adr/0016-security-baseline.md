# ADR-0016: Security Baseline

## Status
Accepted

## Context
Input and secret handling must be strict.

## Decision
Pydantic validation on all inputs. ORM-only SQL access. Secrets never logged or committed. HTTPS in staging/prod. Evidence uploads validated by MIME type and size.

## Consequences
- Reduced injection and data leakage risk.
- Clear upload constraints.
