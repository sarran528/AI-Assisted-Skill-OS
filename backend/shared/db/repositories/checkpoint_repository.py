from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import CheckpointState


class CheckpointRepository:
    @staticmethod
    async def get_checkpoint_state(
        session: AsyncSession,
        roadmap_id: UUID,
        checkpoint_id: str,
    ) -> CheckpointState | None:
        stmt = (
            select(CheckpointState)
            .where(CheckpointState.roadmap_id == roadmap_id)
            .where(CheckpointState.checkpoint_id == checkpoint_id)
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def update_checkpoint_state(
        session: AsyncSession,
        roadmap_id: UUID,
        checkpoint_id: str,
        status: str,
        result_payload: dict | None,
    ) -> None:
        """This function is called only by backend/orchestration/orchestrator.py."""
        state = await CheckpointRepository.get_checkpoint_state(session, roadmap_id, checkpoint_id)
        now = datetime.now(timezone.utc)
        if state is None:
            created = CheckpointState(
                roadmap_id=roadmap_id,
                phase_slug=(result_payload or {}).get("phase_slug", ""),
                checkpoint_id=checkpoint_id,
                status=status,
                attempts=1,
                last_result=result_payload,
                updated_at=now,
            )
            session.add(created)
            await session.commit()
            return

        await session.execute(
            update(CheckpointState)
            .where(CheckpointState.id == state.id)
            .values(
                status=status,
                attempts=state.attempts + 1,
                last_result=result_payload,
                updated_at=now,
            )
        )
        await session.commit()

    @staticmethod
    async def get_all_phase_checkpoints(
        session: AsyncSession,
        roadmap_id: UUID,
        phase_slug: str,
    ) -> list[CheckpointState]:
        stmt = (
            select(CheckpointState)
            .where(CheckpointState.roadmap_id == roadmap_id)
            .where(CheckpointState.phase_slug == phase_slug)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def all_phase_checkpoints_passed(
        session: AsyncSession,
        roadmap_id: UUID,
        phase_slug: str,
    ) -> bool:
        checkpoints = await CheckpointRepository.get_all_phase_checkpoints(session, roadmap_id, phase_slug)
        return bool(checkpoints) and all(item.status == "passed" for item in checkpoints)
