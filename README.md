# AI-Assisted-Skill-OS

## Local setup

1. Copy env example:

```
cp .env.example .env.local
```

2. Load env with direnv:

```
direnv allow
```

3. Run backend API:

```
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Run Celery worker:

```
celery -A backend.shared.queue.celery_app worker --loglevel=INFO
```

5. Apply migrations:

```
alembic -c backend/alembic.ini upgrade head
```