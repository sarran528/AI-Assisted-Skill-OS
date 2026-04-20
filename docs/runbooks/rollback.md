# Rollback Runbook

## Preconditions
- A database snapshot is taken before production migrations.
- The previous Docker image SHA is known.

## Steps
1. Redeploy the previous Docker image SHA.
2. Run `alembic downgrade -1` (or to a specific revision).
3. Verify the service health and key endpoints.

## Notes
- Test downgrade paths in staging before production.
