from uuid import UUID

from sqlalchemy import delete

from backend.roadmap.service import sync_create_roadmap
from backend.shared.db.engine import SyncSessionLocal
from backend.shared.db.models import RevokedAccessToken
from backend.shared.errors import BusinessError, SystemError
from backend.shared.queue.celery_app import celery_app
from backend.validation.service import sync_run_checkpoint_validation


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def generate_roadmap_task(self, user_id: str, skill_id: str) -> dict:
    try:
        with SyncSessionLocal() as db:
            result = sync_create_roadmap(db, UUID(user_id), skill_id)
            return {"roadmap_id": str(result["id"]), "status": "completed"}
    except BusinessError as exc:
        return {
            "status": "failed",
            "error": exc.code,
            "message": str(exc),
            "context": exc.context,
        }
    except SystemError as exc:
        return {
            "status": "failed",
            "error": "system_error",
            "message": str(exc),
            "context": exc.context,
        }
    except Exception as exc:  # pragma: no cover
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {
            "status": "failed",
            "error": "max_retries_exceeded",
            "message": str(exc),
            "context": {},
        }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def validate_checkpoint_task(self, session_id: str, checkpoint_id: str) -> dict:
    try:
        with SyncSessionLocal() as db:
            result = sync_run_checkpoint_validation(db, UUID(session_id), checkpoint_id)
            return {
                "passed": bool(result.get("passed", False)),
                "reason": result.get("reason"),
                "status": "completed",
            }
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)


@celery_app.task
def cleanup_expired_tokens_task() -> None:
    from datetime import datetime, timezone

    with SyncSessionLocal() as db:
        db.execute(
            delete(RevokedAccessToken).where(
                RevokedAccessToken.expires_at < datetime.now(timezone.utc)
            )
        )
        db.commit()