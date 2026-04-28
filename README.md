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

4. Configure Inngest queue settings in `.env.local`:

```
USE_INNGEST_QUEUE=true
INNGEST_EVENT_BASE_URL=https://inn.gs/e
INNGEST_EVENT_KEY=<your_inngest_event_key>
```

5. Apply migrations:

```
alembic -c backend/alembic.ini upgrade head
```