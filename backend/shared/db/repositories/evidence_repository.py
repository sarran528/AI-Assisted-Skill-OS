from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Evidence


class EvidenceRepository:
    @staticmethod
    async def create(session: AsyncSession, data: dict) -> Evidence:
        model = Evidence(**data)
        session.add(model)
        await session.flush()
        await session.commit()
        await session.refresh(model)
        return model

    @staticmethod
    async def get_by_session(session: AsyncSession, session_id: UUID) -> list[Evidence]:
        result = await session.execute(select(Evidence).where(Evidence.session_id == session_id))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_checkpoint(
        session: AsyncSession,
        session_id: UUID,
        checkpoint_id: str,
    ) -> list[Evidence]:
        stmt = (
            select(Evidence)
            .where(Evidence.session_id == session_id)
            .where(Evidence.checkpoint_id == checkpoint_id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_validated(session: AsyncSession, evidence_id: UUID, result: dict) -> None:
        await session.execute(
            update(Evidence)
            .where(Evidence.id == evidence_id)
            .values(
                validated=True,
                validation_result=result,
                validated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    @staticmethod
    async def get_unvalidated(session: AsyncSession) -> list[Evidence]:
        result = await session.execute(select(Evidence).where(Evidence.validated == False))
        return list(result.scalars().all())
