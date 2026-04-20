from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.roadmap.schemas import GeneratedRoadmap
from backend.shared.db.models import Roadmap


class RoadmapRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        roadmap: GeneratedRoadmap,
        user_id: UUID,
        parameters_id: UUID,
    ) -> Roadmap:
        model = Roadmap(
            user_id=user_id,
            skill_id=roadmap.skill_id,
            template_version=roadmap.template_version,
            profile_version=roadmap.profile_version,
            parameters_id=parameters_id,
            structure=roadmap.model_dump(mode="json"),
            fingerprint=roadmap.fingerprint,
            status="active",
        )
        session.add(model)
        await session.flush()
        await session.commit()
        await session.refresh(model)
        return model

    @staticmethod
    async def get_active(session: AsyncSession, user_id: UUID, skill_id: str) -> Roadmap | None:
        stmt = (
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .where(Roadmap.skill_id == skill_id)
            .where(Roadmap.status == "active")
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_id(session: AsyncSession, roadmap_id: UUID) -> Roadmap | None:
        return await session.get(Roadmap, roadmap_id)

    @staticmethod
    async def update_status(session: AsyncSession, roadmap_id: UUID, status: str) -> None:
        """This function is called only by backend/orchestration/orchestrator.py."""
        values: dict[str, object] = {"status": status}
        if status == "completed":
            values["completed_at"] = datetime.now(timezone.utc)
        await session.execute(update(Roadmap).where(Roadmap.id == roadmap_id).values(**values))
        await session.commit()

    @staticmethod
    async def update_phase_status(
        session: AsyncSession,
        roadmap_id: UUID,
        phase_slug: str,
        status: str,
    ) -> None:
        """This function is called only by backend/orchestration/orchestrator.py."""
        roadmap = await session.get(Roadmap, roadmap_id)
        if roadmap is None:
            return

        structure = dict(roadmap.structure)
        phases = dict(structure.get("phases", {}))
        phase = dict(phases.get(phase_slug, {}))
        if not phase:
            return
        phase["status"] = status
        phases[phase_slug] = phase
        structure["phases"] = phases

        await session.execute(
            update(Roadmap)
            .where(Roadmap.id == roadmap_id)
            .values(structure=structure)
        )
        await session.commit()

    @staticmethod
    async def get_phase_status(session: AsyncSession, roadmap_id: UUID, phase_slug: str) -> str | None:
        roadmap = await session.get(Roadmap, roadmap_id)
        if roadmap is None:
            return None
        return roadmap.structure.get("phases", {}).get(phase_slug, {}).get("status")

    @staticmethod
    async def advance_phase(
        session: AsyncSession,
        roadmap_id: UUID,
        current_phase_slug: str,
    ) -> None:
        """This function is called only by backend/orchestration/orchestrator.py."""
        roadmap = await session.get(Roadmap, roadmap_id)
        if roadmap is None:
            return

        structure = dict(roadmap.structure)
        phases = list(structure.get("phases", {}).items())
        slugs = [slug for slug, _ in phases]
        if current_phase_slug not in slugs:
            return

        current_idx = slugs.index(current_phase_slug)
        structure["phases"][current_phase_slug]["status"] = "completed"
        if current_idx + 1 < len(slugs):
            next_slug = slugs[current_idx + 1]
            structure["phases"][next_slug]["status"] = "active"
        else:
            await RoadmapRepository.update_status(session, roadmap_id, "completed")
            return

        await session.execute(
            update(Roadmap)
            .where(Roadmap.id == roadmap_id)
            .values(structure=structure)
        )
        await session.commit()
