from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.session.execution import SessionResult, should_generate_tip
from backend.session.schemas import SessionCompleteResponse
from backend.shared.db.models import LearningParameter, Roadmap, Session
from backend.shared.queue.tasks import generate_tip_task
from backend.validation.validators import validate_behavioral_log


async def start_session(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID,
    phase: str,
    technique_id: str,
    attempt_number: int = 1,
) -> Session:
    model = Session(
        roadmap_id=roadmap_id,
        user_id=user_id,
        phase=phase,
        technique_id=technique_id,
        attempt_number=attempt_number,
        status="active",
        started_at=datetime.now(timezone.utc),
        metrics_captured={},
        protocol_steps_completed=[],
        protocol_violations=[],
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


async def submit_metrics(db: AsyncSession, session_id: UUID, metrics_payload: dict) -> Session:
    session = await db.scalar(select(Session).where(Session.id == session_id))
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    merged = dict(session.metrics_captured or {})
    merged.update(metrics_payload)
    session.metrics_captured = merged
    await db.commit()
    await db.refresh(session)
    return session


async def complete_session(
    db: AsyncSession,
    session_id: UUID,
    completed_steps: list[str],
) -> SessionCompleteResponse:
    session = await db.scalar(select(Session).where(Session.id == session_id))
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    roadmap = await db.scalar(select(Roadmap).where(Roadmap.id == session.roadmap_id))
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    params = await db.scalar(select(LearningParameter).where(LearningParameter.id == roadmap.parameters_id))
    if params is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning parameters not found")

    metrics = session.metrics_captured or {}

    protocol_steps = []
    phase_payload = (roadmap.structure or {}).get("phases", {}).get(session.phase, {})
    for technique in phase_payload.get("techniques", []) if isinstance(phase_payload, dict) else []:
        if technique.get("technique_id") == session.technique_id:
            protocol_steps = list(technique.get("protocol_steps") or [])
            break

    retry_count = metrics.get("retry_count", metrics.get("retry", 0))
    protocol_result = validate_behavioral_log(
        {
            "steps_completed": completed_steps,
            "retry_count": retry_count,
            "retry_limit": int(params.retry_limit),
        },
        required_steps=protocol_steps,
    )

    metrics_passed = bool(metrics.get("passed", False))
    if "accuracy" in metrics:
        metrics_passed = float(metrics.get("accuracy", 0.0) or 0.0) >= float(params.error_tolerance_threshold)
    passed = metrics_passed and protocol_result.passed
    if not protocol_result.passed:
        failure_reason = "protocol_violation"
    else:
        failure_reason = str(metrics.get("failure_reason") or session.failure_reason or "metric_threshold")

    result = SessionResult(
        passed=passed,
        failure_reason=failure_reason,
    )

    session.protocol_steps_completed = completed_steps
    session.protocol_violations = [] if protocol_result.passed else [protocol_result.reason]
    session.status = "failed" if session.protocol_violations or not passed else "completed"
    session.failure_reason = None if passed else failure_reason
    session.ended_at = datetime.now(timezone.utc)

    tip_pending = False
    if should_generate_tip(result, session, params):
        generate_tip_task.delay(
            str(session.id),
            roadmap.skill_id,
            session.technique_id,
            failure_reason,
            session.metrics_captured or {},
            str(params.id),
        )
        tip_pending = True

    await db.commit()

    return SessionCompleteResponse(
        session_id=session.id,
        status=session.status,
        passed=passed,
        failure_reason=session.failure_reason,
        tip_pending=tip_pending,
        tip_poll_url=f"/tip/{session.id}" if tip_pending else None,
    )


async def get_session_status(db: AsyncSession, session_id: UUID) -> Session | None:
    return await db.scalar(select(Session).where(Session.id == session_id))


async def list_recent_sessions(db: AsyncSession, user_id: UUID, limit: int = 5) -> list[Session]:
    stmt = (
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
