"""Repository for skill research objects."""
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models.skill_research import SkillResearchObjectModel
from backend.skill.intelligence import SkillResearchObject


class SkillResearchRepository:
    """Database access layer for skill research objects."""

    @staticmethod
    async def create(
        session: AsyncSession, obj: SkillResearchObject
    ) -> SkillResearchObjectModel:
        """
        Create new skill research record.

        Args:
            session: Database session
            obj: SkillResearchObject to persist

        Returns:
            Created model instance

        Raises:
            sqlalchemy.exc.IntegrityError: If FK or unique constraints violated
        """
        model = SkillResearchObjectModel(
            user_id=obj.user_id,
            skill_id=obj.skill_id,
            profile_version=obj.profile_version,
            payload=obj.model_dump(mode="json"),
        )
        session.add(model)
        await session.flush()
        await session.commit()
        return model

    @staticmethod
    async def get_latest(
        session: AsyncSession, user_id: UUID, skill_id: str
    ) -> SkillResearchObjectModel | None:
        """
        Fetch latest research object for user and skill.

        Args:
            session: Database session
            user_id: User identifier
            skill_id: Skill identifier

        Returns:
            Latest SkillResearchObjectModel or None if not found
        """
        stmt = (
            select(SkillResearchObjectModel)
            .where(SkillResearchObjectModel.user_id == user_id)
            .where(SkillResearchObjectModel.skill_id == skill_id)
            .order_by(desc(SkillResearchObjectModel.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_id(
        session: AsyncSession, research_id: UUID
    ) -> SkillResearchObjectModel | None:
        """
        Fetch research object by ID.

        Args:
            session: Database session
            research_id: Research object ID

        Returns:
            SkillResearchObjectModel or None
        """
        return await session.get(SkillResearchObjectModel, research_id)
