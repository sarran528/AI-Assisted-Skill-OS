from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.schemas import LearningParameters
from backend.orchestration.orchestrator import transition_session
from backend.roadmap.schemas import GeneratedRoadmap
from backend.session.execution import (
    SessionMetrics,
    SessionResult,
    compute_session_result,
    validate_protocol_adherence,
)
from backend.shared.audit import log_audit_event
from backend.shared.db.models import CognitiveProfile, LearningParameter, Roadmap
from backend.shared.db.repositories.session_repository import SessionRepository
from backend.shared.errors import BusinessError


async def _fetch_learning_params_for_session(
    db: AsyncSession,
    user_id: UUID,
    skill_id: str,
) -> LearningParameters:
    stmt = (
        select(LearningParameter)
        .join(CognitiveProfile, CognitiveProfile.id == LearningParameter.profile_id)
        .where(CognitiveProfile.user_id == user_id)
        .where(LearningParameter.skill_id == skill_id)
        .order_by(desc(CognitiveProfile.version), desc(LearningParameter.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    model = result.scalars().first()
    if model is None:
        raise BusinessError("parameters_required", "Learning parameters are required")

    payload: dict[str, float | int] = {}
    for field in LearningParameters.model_fields:
        value = getattr(model, field)
        payload[field] = value if isinstance(value, int) else float(value)
    return LearningParameters.model_validate(payload)


async def start_session(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID,
    phase: str,
    technique_id: str,
) -> UUID:
    active = await SessionRepository.get_active_session(db, user_id)
    if active is not None:
        raise BusinessError("session_already_active", "User already has an active session")

    roadmap = await db.get(Roadmap, roadmap_id)
    if roadmap is None or roadmap.status != "active":
        raise BusinessError("roadmap_not_active", "Roadmap must be active")

    phase_status = roadmap.structure.get("phases", {}).get(phase, {}).get("status")
    if phase_status != "active":
        raise BusinessError("phase_not_active", "Requested phase is not currently active")

    session = await SessionRepository.create(
        db,
        {
            "roadmap_id": roadmap_id,
            "user_id": user_id,
            "phase": phase,
            "technique_id": technique_id,
            "status": "pending",
        },
    )
    await transition_session(db, session.id, "active")
    await log_audit_event(
        db,
        user_id=str(user_id),
        action="session.started",
        entity_type="session",
        entity_id=str(session.id),
        ip_address=None,
    )
    return session.id


async def submit_metrics(db: AsyncSession, session_id: UUID, metrics_payload: dict) -> None:
    await SessionRepository.append_metrics(db, session_id, metrics_payload)


async def complete_session(
    db: AsyncSession,
    redis,
    session_id: UUID,
    completed_steps: list[str],
) -> SessionResult:
    del redis
    session = await SessionRepository.get_by_id(db, session_id)
    if session is None:
        raise BusinessError("session_not_found", "Session not found")

    roadmap = await db.get(Roadmap, session.roadmap_id)
    if roadmap is None:
        raise BusinessError("roadmap_not_found", "Roadmap not found")

    generated = GeneratedRoadmap.model_validate(roadmap.structure)
    phase = generated.phases.get(session.phase)
    if phase is None:
        raise BusinessError("phase_not_found", "Phase not found in roadmap")

    technique = next((tech for tech in phase.techniques if tech.technique_id == session.technique_id), None)
    if technique is None:
        raise BusinessError("technique_not_found", "Technique not found in selected phase")
    required_steps = technique.protocol_steps

    params = await _fetch_learning_params_for_session(db, session.user_id, roadmap.skill_id)
    adherence_ok, _missing = validate_protocol_adherence(completed_steps, required_steps)

    all_records = (session.metrics_captured or {}).get("records", [])
    latest = all_records[-1] if all_records else {}
    metrics = SessionMetrics(
        accuracy_pct=latest.get("accuracy_pct"),
        time_taken_seconds=latest.get("time_taken_seconds"),
        error_count=latest.get("error_count"),
        step_completion_rate=1.0 if not required_steps else len(completed_steps) / len(required_steps),
        retry_count=int(latest.get("retry_count", 0)),
        raw_signals=latest,
    )
    result = compute_session_result(metrics, params, adherence_ok)

    await SessionRepository.set_completed_steps(db, session_id, completed_steps)
    if result.passed:
        await transition_session(db, session_id, "completed")
        action = "session.completed"
    else:
        await transition_session(db, session_id, "failed", result.failure_reason)
        action = "session.failed"

    await log_audit_event(
        db,
        user_id=str(session.user_id),
        action=action,
        entity_type="session",
        entity_id=str(session.id),
        ip_address=None,
        metadata={"failure_reason": result.failure_reason, "metric_details": result.metric_details},
    )
    return result


async def get_session_status(db: AsyncSession, session_id: UUID) -> dict:
    session = await SessionRepository.get_by_id(db, session_id)
    if session is None:
        raise BusinessError("session_not_found", "Session not found")

    return {
        "session_id": str(session.id),
        "roadmap_id": str(session.roadmap_id),
        "phase": session.phase,
        "technique_id": session.technique_id,
        "status": session.status,
        "failure_reason": session.failure_reason,
        "metrics_captured": session.metrics_captured,
    }
