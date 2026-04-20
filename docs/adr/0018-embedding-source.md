# ADR-0018: Embedding Source

## Status
Accepted

## Context
The embedding model must be fixed, including its output dimension, and recorded for index consistency.

## Decision
Use OpenAI text-embedding-3-small with a 1536 dimension output.

## Consequences
- Changing the model requires a full re-index.
- Vector column dimension must match the model output.
