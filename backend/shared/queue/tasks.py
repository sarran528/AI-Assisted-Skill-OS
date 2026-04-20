from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import text

from backend.shared.queue.celery_app import celery_app
from backend.shared.db.engine import SyncSessionLocal
from backend.support.tip_service import map_failure_type
from backend.validation.service import sync_run_checkpoint_validation


def sync_create_roadmap(db, user_id: UUID, skill_id: str) -> dict:
    from backend.roadmap.service import sync_create_roadmap as _sync_create_roadmap

    return _sync_create_roadmap(db, user_id, skill_id)


@celery_app.task
def placeholder_task() -> str:
    return "ok"


@celery_app.task
def generate_roadmap_task(user_id: str, skill_id: str) -> dict:
    with SyncSessionLocal() as db:
        result = sync_create_roadmap(db, UUID(user_id), skill_id)
    return {"roadmap_id": result["id"], "status": "completed"}


@celery_app.task
def validate_checkpoint_task(session_id: str, checkpoint_id: str) -> dict:
    with SyncSessionLocal() as db:
        result = sync_run_checkpoint_validation(db, UUID(session_id), checkpoint_id)
    return {**result, "status": "completed"}


async def _generate_tip_async(
    session_id: str,
    skill_id: str,
    technique_id: str,
    failure_reason: str,
    session_metrics: dict,
    params_id: str,
) -> dict:
    del session_id, skill_id, technique_id, params_id
    return {
        "tip": "Focus on one protocol step at a time and reduce pace.",
        "severity": "moderate",
        "failure_type": map_failure_type(failure_reason, session_metrics),
    }


@celery_app.task
def generate_tip_task(
    session_id: str,
    skill_id: str,
    technique_id: str,
    failure_reason: str,
    session_metrics: dict,
    params_id: str,
) -> dict:
    return asyncio.run(
        _generate_tip_async(
            session_id=session_id,
            skill_id=skill_id,
            technique_id=technique_id,
            failure_reason=failure_reason,
            session_metrics=session_metrics,
            params_id=params_id,
        )
    )


@celery_app.task
def cleanup_expired_tokens_task() -> None:
    with SyncSessionLocal() as db:
        db.execute(
            text(
                "DELETE FROM refresh_tokens "
                "WHERE expires_at < now() "
                "AND revoked_at IS NOT NULL"
            )
        )
        db.commit()


@celery_app.task
def prefetch_resources_task(user_id: str, skill_id: str, phase: str) -> dict:
    del user_id, skill_id, phase
    return {"status": "queued"}
