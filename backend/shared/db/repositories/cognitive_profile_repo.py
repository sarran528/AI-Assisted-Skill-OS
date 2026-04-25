from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models.cognitive_profile import CognitiveProfile


class CognitiveProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_cognitive_profile(self, user_id: UUID) -> CognitiveProfile:
        profile = CognitiveProfile(user_id=user_id, profile={})
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile
