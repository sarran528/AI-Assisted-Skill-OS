"""Repository for baseline skill state database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models.baseline_skill_state import BaselineSkillState as BaselineSkillStateModel


class GroundingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_baseline(
        self,
        user_id: UUID,
        skill_id: str,
        exposure_score: float,
        declarative_score: float,
        confidence_score: float,
        perceived_level: float,
        actual_level: float,
        confidence_bias: float,
        raw_responses: dict | None = None,
    ) -> BaselineSkillStateModel:
        """Create a new baseline skill state record."""
        baseline = BaselineSkillStateModel(
            user_id=user_id,
            skill_id=skill_id,
            exposure_score=exposure_score,
            declarative_score=declarative_score,
            confidence_score=confidence_score,
            perceived_level=perceived_level,
            actual_level=actual_level,
            confidence_bias=confidence_bias,
            raw_responses=raw_responses,
        )
        self.session.add(baseline)
        await self.session.commit()
        await self.session.refresh(baseline)
        return baseline

    async def get_latest_baseline(
        self,
        user_id: UUID,
        skill_id: str,
    ) -> Optional[BaselineSkillStateModel]:
        """Get the most recent baseline state for user + skill."""
        result = await self.session.execute(
            select(BaselineSkillStateModel)
            .where(BaselineSkillStateModel.user_id == user_id)
            .where(BaselineSkillStateModel.skill_id == skill_id)
            .order_by(BaselineSkillStateModel.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, baseline_id: UUID) -> Optional[BaselineSkillStateModel]:
        """Get baseline by UUID."""
        result = await self.session.execute(
            select(BaselineSkillStateModel).where(BaselineSkillStateModel.id == baseline_id)
        )
        return result.scalar_one_or_none()
