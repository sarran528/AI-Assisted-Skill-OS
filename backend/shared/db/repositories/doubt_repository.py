from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import DoubtLog


@dataclass(slots=True)
class DoubtLogCreate:
    user_id: UUID
    session_id: UUID | None
    skill_id: str
    phase: str | None
    question: str
    answer: str
    chunks_used: int
    confidence: str


class DoubtRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: DoubtLogCreate) -> DoubtLog:
        model = DoubtLog(
            user_id=data.user_id,
            session_id=data.session_id,
            skill_id=data.skill_id,
            phase=data.phase,
            question=data.question,
            answer=data.answer,
            chunks_used=data.chunks_used,
            confidence=data.confidence,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model
