from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Roadmap
from backend.shared.queue.tasks import prefetch_resources_task


async def transition_roadmap_phase(
    db: AsyncSession,
    roadmap_id,
    user_id,
    phase: str,
) -> Roadmap:
    roadmap = await db.scalar(select(Roadmap).where(Roadmap.id == roadmap_id, Roadmap.user_id == user_id))
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    structure = dict(roadmap.structure or {})
    structure["active_phase"] = phase
    roadmap.structure = structure

    await db.commit()
    await db.refresh(roadmap)

    prefetch_resources_task.delay(str(user_id), roadmap.skill_id, phase)
    return roadmap
