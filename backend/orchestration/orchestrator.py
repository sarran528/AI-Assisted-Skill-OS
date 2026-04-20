from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.orchestration.state_machine import (
    CHECKPOINT_TRANSITIONS,
    ROADMAP_PHASE_TRANSITIONS,
    SESSION_TRANSITIONS,
    validate_transition,
)
from backend.shared.audit import log_audit_event
from backend.shared.db.repositories.checkpoint_repository import CheckpointRepository
from backend.shared.db.repositories.roadmap_repository import RoadmapRepository
from backend.shared.db.repositories.session_repository import SessionRepository


async def transition_session(
    db: AsyncSession,
    session_id: UUID,
    target_status: str,
    failure_reason: str | None = None,
) -> None:
    session = await SessionRepository.get_by_id(db, session_id)
    if session is None:
        return
    validate_transition(session.status, target_status, SESSION_TRANSITIONS)
    await SessionRepository.update_status(db, session_id, target_status, failure_reason)
    await log_audit_event(
        db,
        user_id=str(session.user_id),
        action=f"session.{target_status}",
        entity_type="session",
        entity_id=str(session_id),
        ip_address=None,
        metadata={"failure_reason": failure_reason},
    )


async def transition_checkpoint(
    db: AsyncSession,
    roadmap_id: UUID,
    checkpoint_id: str,
    target_status: str,
    result: dict | None = None,
) -> None:
    current = await CheckpointRepository.get_checkpoint_state(db, roadmap_id, checkpoint_id)
    current_status = current.status if current else "pending"
    validate_transition(current_status, target_status, CHECKPOINT_TRANSITIONS)
    await CheckpointRepository.update_checkpoint_state(
        db,
        roadmap_id,
        checkpoint_id,
        target_status,
        result,
    )


async def transition_roadmap_phase(
    db: AsyncSession,
    roadmap_id: UUID,
    phase_slug: str,
    target_status: str,
) -> None:
    current_status = await RoadmapRepository.get_phase_status(db, roadmap_id, phase_slug)
    if current_status is None:
        return
    validate_transition(current_status, target_status, ROADMAP_PHASE_TRANSITIONS)
    await RoadmapRepository.update_phase_status(db, roadmap_id, phase_slug, target_status)

    if target_status == "completed":
        await unlock_next_phase(db, roadmap_id, phase_slug)


async def unlock_next_phase(db: AsyncSession, roadmap_id: UUID, completed_phase_slug: str) -> None:
    roadmap = await RoadmapRepository.get_by_id(db, roadmap_id)
    if roadmap is None:
        return

    phases = list(roadmap.structure.get("phases", {}).keys())
    if completed_phase_slug not in phases:
        return

    idx = phases.index(completed_phase_slug)
    if idx + 1 >= len(phases):
        await RoadmapRepository.update_status(db, roadmap_id, "completed")
        return

    next_phase = phases[idx + 1]
    await transition_roadmap_phase(db, roadmap_id, next_phase, "active")


async def check_phase_completion(db: AsyncSession, roadmap_id: UUID, phase_slug: str) -> bool:
    completed = await CheckpointRepository.all_phase_checkpoints_passed(db, roadmap_id, phase_slug)
    if completed:
        await transition_roadmap_phase(db, roadmap_id, phase_slug, "completed")
    return completed
