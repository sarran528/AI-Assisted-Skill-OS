from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.schemas import LearningParameters
from backend.orchestration.orchestrator import transition_session
from backend.session.execution import (
    SessionMetrics,
    compute_session_result,
    should_generate_tip,
    validate_protocol_adherence,
)
from backend.session.schemas import SessionCompleteResponse
from backend.shared.db.models import LearningParameter, Roadmap, Session
from backend.shared.db.repositories.session_repository import SessionRepository
from backend.shared.errors import BusinessError
from backend.shared.audit import log_audit_event
from backend.shared.queue.tasks import generate_tip_task


async def start_session(
    db: AsyncSession,
    user_id: UUID,
    roadmap_id: UUID,
    phase: str,
    technique_id: str,
    attempt_number: int = 1,
) -> Session:
    active = await SessionRepository.get_active_session(db, user_id)
    if active is not None:
        raise BusinessError("session_active", "User already has an active session")

    return await SessionRepository.create(
        db,
        {
            "roadmap_id": roadmap_id,
            "user_id": user_id,
            "phase": phase,
            "technique_id": technique_id,
            "attempt_number": attempt_number,
            "status": "active",
            "started_at": datetime.now(timezone.utc),
            "metrics_captured": {},
            "protocol_steps_completed": [],
            "protocol_violations": [],
        },
    )


async def submit_metrics(db: AsyncSession, session_id: UUID, metrics_payload: dict) -> Session:
    await SessionRepository.append_metrics(db, session_id, metrics_payload)
    session = await SessionRepository.get_by_id(db, session_id)
    if session is None:
        raise BusinessError("session_not_found", "Session not found")
    return session


async def _fetch_learning_params_for_session(db: AsyncSession, session: Session) -> LearningParameters:
    roadmap = await db.get(Roadmap, session.roadmap_id)
    if roadmap is None:
        raise BusinessError("roadmap_not_found", "Roadmap not found")

    params = await db.get(LearningParameter, roadmap.structure.get("parameters_id"))
    if params is None:
        raise BusinessError("learning_parameters_not_found", "Learning parameters not found")

    return LearningParameters(
        difficulty_slope=float(params.difficulty_slope),
        phase_pacing=float(params.phase_pacing),
        entry_phase_offset=float(params.entry_phase_offset),
        repetition_intensity=float(params.repetition_intensity),
        session_duration=float(params.session_duration),
        micro_session_enabled=int(params.micro_session_enabled),
        fatigue_threshold=float(params.fatigue_threshold),
        break_frequency=float(params.break_frequency),
        technique_density=float(params.technique_density),
        concurrent_technique_limit=int(params.concurrent_technique_limit),
        abstraction_level=float(params.abstraction_level),
        instruction_granularity=float(params.instruction_granularity),
        checkpoint_frequency=float(params.checkpoint_frequency),
        checkpoint_rigidity=float(params.checkpoint_rigidity),
        error_tolerance_threshold=float(params.error_tolerance_threshold),
        retry_limit=int(params.retry_limit),
        drill_depth=float(params.drill_depth),
        variation_intensity=float(params.variation_intensity),
        stress_exposure_rate=float(params.stress_exposure_rate),
        simulation_complexity=float(params.simulation_complexity),
        feedback_detail_level=float(params.feedback_detail_level),
        correction_delay_window=float(params.correction_delay_window),
        hint_activation_threshold=float(params.hint_activation_threshold),
        precision_requirement=float(params.precision_requirement),
        speed_requirement=float(params.speed_requirement),
        coordination_complexity=float(params.coordination_complexity),
        adaptation_sensitivity=float(params.adaptation_sensitivity),
        risk_zone_trigger_level=float(params.risk_zone_trigger_level),
        regression_policy_strength=float(params.regression_policy_strength),
        phase_transition_sensitivity=float(params.phase_transition_sensitivity),
        complexity_escalation_trigger=float(params.complexity_escalation_trigger),
        plateau_detection_threshold=float(params.plateau_detection_threshold),
        stability_requirement_before_advance=float(params.stability_requirement_before_advance),
    )


async def complete_session(
    db: AsyncSession,
    current_user: object | None,
    session_id: UUID,
    completed_steps: list[str],
) -> SessionCompleteResponse:
    del current_user
    session = await SessionRepository.get_by_id(db, session_id)
    if session is None:
        raise BusinessError("session_not_found", "Session not found")

    roadmap = await db.get(Roadmap, session.roadmap_id)
    if roadmap is None:
        raise BusinessError("roadmap_not_found", "Roadmap not found")
    phase = (roadmap.structure.get("phases") or {}).get(session.phase) or {}
    techniques = phase.get("techniques") or []
    technique = next((t for t in techniques if t.get("technique_id") == session.technique_id), None)
    if technique is None:
        raise BusinessError("technique_not_found", "Technique not found")
    expected_steps = technique.get("protocol_steps") or []
    adherence_ok, missing_steps = validate_protocol_adherence(completed_steps, expected_steps)

    params = await _fetch_learning_params_for_session(db, session)
    latest_metrics = (session.metrics_captured or {}).get("records", [{}])[-1]
    metrics = SessionMetrics(
        accuracy_pct=float(latest_metrics.get("accuracy_pct", 0.0) or 0.0),
        time_taken_seconds=float(latest_metrics.get("time_taken_seconds", 0.0) or 0.0),
        error_count=int(latest_metrics.get("error_count", 0) or 0),
        step_completion_rate=(1.0 if adherence_ok else 0.0),
        retry_count=int(latest_metrics.get("retry_count", 0) or 0),
        raw_signals=latest_metrics,
    )
    result = compute_session_result(metrics, params, adherence_ok=adherence_ok)

    await SessionRepository.set_completed_steps(db, session_id, completed_steps)

    tip_pending = False
    if should_generate_tip(result, session, params):
        generate_tip_task.delay(
            str(session.id),
            roadmap.skill_id,
            session.technique_id,
            result.failure_reason or "metric_threshold",
            latest_metrics,
            str((roadmap.structure or {}).get("parameters_id")),
        )
        tip_pending = True

    if result.passed:
        await transition_session(db, session_id, "completed")
    else:
        await transition_session(db, session_id, "failed", result.failure_reason)
        session.protocol_violations = missing_steps

    await log_audit_event(
        db,
        user_id=str(session.user_id),
        action="session.completed",
        entity_type="session",
        entity_id=str(session_id),
        ip_address=None,
        metadata={"passed": result.passed, "failure_reason": result.failure_reason},
    )

    return SessionCompleteResponse(
        session_id=session.id,
        status="completed" if result.passed else "failed",
        passed=result.passed,
        failure_reason=result.failure_reason,
        tip_pending=tip_pending,
        tip_poll_url=f"/support/tip/{session.id}" if tip_pending else None,
    )


async def get_session_status(db: AsyncSession, session_id: UUID) -> Session | None:
    return await SessionRepository.get_by_id(db, session_id)
