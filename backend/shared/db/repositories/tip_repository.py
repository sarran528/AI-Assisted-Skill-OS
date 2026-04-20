from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import TipLog


@dataclass(slots=True)
class TipLogCreate:
    session_id: UUID
    user_id: UUID
    technique_id: str
    failure_type: str
    attempt_number: int
    tip: str
    severity: str
    target_step: str | None
    chunks_used: int


class TipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: TipLogCreate) -> TipLog:
        model = TipLog(
            session_id=data.session_id,
            user_id=data.user_id,
            technique_id=data.technique_id,
            failure_type=data.failure_type,
            attempt_number=data.attempt_number,
            tip=data.tip,
            severity=data.severity,
            target_step=data.target_step,
            chunks_used=data.chunks_used,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def get_latest_for_session(self, session_id: UUID) -> TipLog | None:
        result = await self.session.execute(
            select(TipLog)
            .where(TipLog.session_id == session_id)
            .order_by(desc(TipLog.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
