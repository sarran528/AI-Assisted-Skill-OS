from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import select

from backend.shared.db.engine import SessionLocal
from backend.shared.db.models import LearningParameter, Session
from backend.shared.queue.celery_app import celery_app
from backend.support.resource_service import get_resources
from backend.support.tip_service import generate_tip


@celery_app.task
def placeholder_task() -> str:
    return "ok"


@celery_app.task
def generate_roadmap_task(job_id: str) -> str:
    return job_id


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def prefetch_resources_task(self, user_id: str, skill_id: str, phase: str) -> dict:
    try:
        return asyncio.run(_prefetch_resources_async(user_id, skill_id, phase))
    except Exception as exc:  # pragma: no cover - celery retry path
        raise self.retry(exc=exc)


async def _prefetch_resources_async(user_id: str, skill_id: str, phase: str) -> dict:
    async with SessionLocal() as db:
        response = await get_resources(
            db=db,
            skill_id=skill_id,
            phase=phase,
            user_query=None,
            current_user={"user": {"id": user_id}},
        )
    return {"resources": len(response.resources), "skill_id": skill_id, "phase": phase}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def generate_tip_task(
    self,
    session_id: str,
    skill_id: str,
    technique_id: str,
    failure_reason: str,
    session_metrics: dict,
    params_id: str,
) -> dict:
    try:
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
    except Exception as exc:  # pragma: no cover - celery retry path
        raise self.retry(exc=exc)


async def _generate_tip_async(
    session_id: str,
    skill_id: str,
    technique_id: str,
    failure_reason: str,
    session_metrics: dict,
    params_id: str,
) -> dict:
    parsed_session_id = UUID(session_id)
    parsed_params_id = UUID(params_id)

    async with SessionLocal() as db:
        session = await db.scalar(select(Session).where(Session.id == parsed_session_id))
        if session is None:
            raise ValueError("Session not found for tip generation")

        params = await db.scalar(select(LearningParameter).where(LearningParameter.id == parsed_params_id))
        if params is None:
            raise ValueError("Learning parameters not found for tip generation")

        result = await generate_tip(
            db=db,
            session_id=parsed_session_id,
            user_id=session.user_id,
            skill_id=skill_id,
            technique_id=technique_id,
            failure_reason=failure_reason,
            session_metrics=session_metrics,
            params=params,
            attempt_number=int(session.attempt_number),
        )

    return {"tip": result.tip, "severity": result.severity, "failure_type": result.failure_type}
