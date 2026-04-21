import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update

from backend.shared.db.engine import SessionLocal
from backend.shared.db.models import Job
from backend.shared.queue.celery_app import celery_app
from backend.validation.engine import validate_checkpoint


@celery_app.task
def placeholder_task() -> str:
    return "ok"


async def _update_job(job_id: UUID, status: str, result: dict | None = None) -> None:
    async with SessionLocal() as session:
        payload = {"status": status}
        if result is not None:
            payload["result"] = json.dumps(result)

        await session.execute(update(Job).where(Job.id == job_id).values(**payload))
        await session.commit()


@celery_app.task
def generate_roadmap_task(job_id: str) -> dict:
    async def _runner() -> dict:
        job_uuid = UUID(job_id)
        await _update_job(job_uuid, "running")
        # Roadmap generation internals are still handled by roadmap services.
        result = {
            "job_id": job_id,
            "status": "completed",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        await _update_job(job_uuid, "completed", result)
        return result

    try:
        return asyncio.run(_runner())
    except Exception as exc:
        try:
            asyncio.run(_update_job(UUID(job_id), "failed", {"error": str(exc)}))
        except Exception:
            pass
        return {"job_id": job_id, "status": "failed", "error": str(exc)}


@celery_app.task
def validate_checkpoint_task(
    session_id: str,
    checkpoint_id: str,
    checkpoint_status: str = "attempted",
    job_id: str | None = None,
) -> dict:
    async def _runner() -> dict:
        if job_id:
            await _update_job(UUID(job_id), "running")

        async with SessionLocal() as session:
            passed, reason = await validate_checkpoint(
                db_session=session,
                session_id=UUID(session_id),
                checkpoint_id=checkpoint_id,
                checkpoint_status=checkpoint_status,
            )

        result = {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "passed": passed,
            "reason": reason,
        }
        if job_id:
            await _update_job(UUID(job_id), "completed" if passed else "failed", result)
        return result

    try:
        return asyncio.run(_runner())
    except Exception as exc:
        if job_id:
            try:
                asyncio.run(_update_job(UUID(job_id), "failed", {"error": str(exc)}))
            except Exception:
                pass
        return {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "passed": False,
            "reason": "task_error",
            "error": str(exc),
        }
