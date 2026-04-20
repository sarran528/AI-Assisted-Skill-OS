from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.assessment.schemas import LearningParameters
from backend.orchestration.orchestrator import check_phase_completion, transition_checkpoint
from backend.roadmap.schemas import GeneratedRoadmap
from backend.shared.audit import log_audit_event
from backend.shared.db.models import (
    CheckpointState,
    CognitiveProfile,
    Evidence,
    LearningParameter,
    Roadmap,
    Session as SessionModel,
)
from backend.shared.errors import BusinessError
from backend.validation.engine import validate_checkpoint
from backend.validation.schemas import ValidationResult
from backend.validation.validators import (
    validate_artifact,
    validate_behavioral_log,
    validate_numeric,
)


async def _fetch_learning_params(db: AsyncSession, user_id: UUID, skill_id: str) -> LearningParameters:
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


def _fetch_learning_params_sync(db: Session, user_id: UUID, skill_id: str) -> LearningParameters:
    stmt = (
        select(LearningParameter)
        .join(CognitiveProfile, CognitiveProfile.id == LearningParameter.profile_id)
        .where(CognitiveProfile.user_id == user_id)
        .where(LearningParameter.skill_id == skill_id)
        .order_by(desc(CognitiveProfile.version), desc(LearningParameter.created_at))
        .limit(1)
    )
    result = db.execute(stmt)
    model = result.scalars().first()
    if model is None:
        raise BusinessError("parameters_required", "Learning parameters are required")

    payload: dict[str, float | int] = {}
    for field in LearningParameters.model_fields:
        value = getattr(model, field)
        payload[field] = value if isinstance(value, int) else float(value)
    return LearningParameters.model_validate(payload)


def _transition_checkpoint_sync(
    db: Session,
    roadmap_id: UUID,
    phase_slug: str,
    checkpoint_id: str,
    target_status: str,
    result_payload: dict,
) -> None:
    now = datetime.now(timezone.utc)
    state = (
        db.execute(
            select(CheckpointState)
            .where(CheckpointState.roadmap_id == roadmap_id)
            .where(CheckpointState.checkpoint_id == checkpoint_id)
            .limit(1)
        )
        .scalars()
        .first()
    )
    if state is None:
        db.add(
            CheckpointState(
                roadmap_id=roadmap_id,
                phase_slug=phase_slug,
                checkpoint_id=checkpoint_id,
                status=target_status,
                attempts=1,
                last_result=result_payload,
                updated_at=now,
            )
        )
        return

    state.status = target_status
    state.attempts = int(state.attempts or 0) + 1
    state.last_result = result_payload
    state.updated_at = now


def _run_artifact_validation_sync(
    payload: dict,
    artifact_url: str,
    checkpoint_description: str,
    pass_criteria: str,
) -> ValidationResult:
    return asyncio.run(
        validate_artifact(
            payload,
            artifact_url=artifact_url,
            checkpoint_description=checkpoint_description,
            pass_criteria=pass_criteria,
        )
    )


def _extract_checkpoint_definition(generated: GeneratedRoadmap, checkpoint_id: str) -> tuple[str, dict]:
    for phase_slug, phase in generated.phases.items():
        for checkpoint in phase.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                payload = checkpoint.model_dump(mode="json")
                payload["required_steps"] = []
                return phase_slug, payload
    raise BusinessError("checkpoint_not_found", f"Checkpoint '{checkpoint_id}' not found")


async def run_checkpoint_validation(
    db: AsyncSession,
    session_id: UUID,
    checkpoint_id: str,
):
    session = await db.get(SessionModel, session_id)
    if session is None:
        raise BusinessError("session_not_found", "Session not found")

    roadmap = await db.get(Roadmap, session.roadmap_id)
    if roadmap is None:
        raise BusinessError("roadmap_not_found", "Roadmap not found")

    generated = GeneratedRoadmap.model_validate(roadmap.structure)
    phase_slug, checkpoint_def = _extract_checkpoint_definition(generated, checkpoint_id)
    params = await _fetch_learning_params(db, session.user_id, roadmap.skill_id)

    await transition_checkpoint(
        db,
        roadmap.id,
        checkpoint_id,
        "attempted",
        result={"phase_slug": phase_slug, "reason": "validation_started"},
    )

    result = await validate_checkpoint(db, session_id, checkpoint_id, params, checkpoint_def)
    target_status = "passed" if result.passed else "failed"
    await transition_checkpoint(
        db,
        roadmap.id,
        checkpoint_id,
        target_status,
        result={"phase_slug": phase_slug, **result.to_dict()},
    )

    await log_audit_event(
        db,
        user_id=str(session.user_id),
        action=f"checkpoint.{target_status}",
        entity_type="checkpoint",
        entity_id=None,
        ip_address=None,
        metadata={"checkpoint_id": checkpoint_id, **result.to_dict()},
    )

    if result.passed:
        await check_phase_completion(db, roadmap.id, phase_slug)
    return result


def sync_run_checkpoint_validation(db: Session, session_id: UUID, checkpoint_id: str) -> dict:
    session = db.get(SessionModel, session_id)
    if session is None:
        raise BusinessError("session_not_found", "Session not found")

    roadmap = db.get(Roadmap, session.roadmap_id)
    if roadmap is None:
        raise BusinessError("roadmap_not_found", "Roadmap not found")

    generated = GeneratedRoadmap.model_validate(roadmap.structure)
    phase_slug, checkpoint_def = _extract_checkpoint_definition(generated, checkpoint_id)
    params = _fetch_learning_params_sync(db, session.user_id, roadmap.skill_id)

    _transition_checkpoint_sync(
        db,
        roadmap.id,
        phase_slug,
        checkpoint_id,
        "attempted",
        {"phase_slug": phase_slug, "reason": "validation_started"},
    )

    evidences = list(
        db.execute(
            select(Evidence)
            .where(Evidence.session_id == session_id)
            .where(Evidence.checkpoint_id == checkpoint_id)
        )
        .scalars()
        .all()
    )

    if not evidences:
        final_result = ValidationResult(
            passed=False,
            threshold=None,
            actual=None,
            reason="no_evidence_submitted",
            evidence_type=checkpoint_def.get("evidence_type", "unknown"),
        )
    else:
        per_evidence_results: list[ValidationResult] = []
        for evidence in evidences:
            payload = dict(evidence.payload or {})
            if evidence.type == "numeric":
                result = validate_numeric(
                    payload,
                    threshold=float(checkpoint_def.get("threshold", 0.0)),
                    pass_criteria=checkpoint_def.get("pass_criteria", ""),
                )
            elif evidence.type == "artifact":
                result = _run_artifact_validation_sync(
                    payload,
                    artifact_url=evidence.artifact_url or "",
                    checkpoint_description=checkpoint_def.get("description", ""),
                    pass_criteria=checkpoint_def.get("pass_criteria", ""),
                )
            else:
                payload["retry_limit"] = int(params.retry_limit)
                result = validate_behavioral_log(
                    payload,
                    required_steps=checkpoint_def.get("required_steps", []),
                )

            evidence.validated = True
            evidence.validation_result = result.to_dict()
            evidence.validated_at = datetime.now(timezone.utc)
            per_evidence_results.append(result)

        if any(not item.passed for item in per_evidence_results):
            final_result = next(item for item in per_evidence_results if not item.passed)
        else:
            first = per_evidence_results[0]
            final_result = ValidationResult(
                passed=True,
                threshold=first.threshold,
                actual=first.actual,
                reason="all_evidence_passed",
                evidence_type=first.evidence_type,
            )

    target_status = "passed" if final_result.passed else "failed"
    _transition_checkpoint_sync(
        db,
        roadmap.id,
        phase_slug,
        checkpoint_id,
        target_status,
        {"phase_slug": phase_slug, **final_result.to_dict()},
    )

    if final_result.passed:
        phase_states = list(
            db.execute(
                select(CheckpointState)
                .where(CheckpointState.roadmap_id == roadmap.id)
                .where(CheckpointState.phase_slug == phase_slug)
            )
            .scalars()
            .all()
        )
        if phase_states and all(state.status == "passed" for state in phase_states):
            structure = dict(roadmap.structure)
            phases = dict(structure.get("phases", {}))
            current_phase = dict(phases.get(phase_slug, {}))
            if current_phase:
                current_phase["status"] = "completed"
                phases[phase_slug] = current_phase
                phase_order = list(phases.keys())
                current_index = phase_order.index(phase_slug)
                if current_index + 1 < len(phase_order):
                    next_slug = phase_order[current_index + 1]
                    next_phase = dict(phases.get(next_slug, {}))
                    if next_phase:
                        next_phase["status"] = "active"
                        phases[next_slug] = next_phase
                else:
                    roadmap.status = "completed"
                    roadmap.completed_at = datetime.now(timezone.utc)
                structure["phases"] = phases
                roadmap.structure = structure

    db.commit()
    return {"passed": bool(final_result.passed), "reason": final_result.reason}
