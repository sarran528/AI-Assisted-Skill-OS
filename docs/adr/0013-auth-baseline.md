# ADR-0013: Auth Baseline

## Status
Accepted

## Context
The system requires secure and simple auth.

## Decision
JWT with RS256. Access token 1 hour, refresh token 30 days in httpOnly SameSite=Strict cookie. All routes except register/login are protected.

## Consequences
- Strong token security.
- Clear middleware enforcement.
