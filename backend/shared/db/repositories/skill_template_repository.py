"""
Repository for skill template database operations.
"""

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import SkillTemplate


class SkillTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_template(self, skill_id: str) -> Optional[SkillTemplate]:
        """Fetch the latest active version of a skill template."""
        result = await self.session.execute(
            select(SkillTemplate)
            .where(SkillTemplate.skill_id == skill_id)
            .where(SkillTemplate.is_active == True)
            .order_by(SkillTemplate.version.desc())
        )
        return result.scalar_one_or_none()

    async def get_template_by_version(
        self, skill_id: str, version: int
    ) -> Optional[SkillTemplate]:
        """Fetch a specific version of a skill template."""
        result = await self.session.execute(
            select(SkillTemplate)
            .where(SkillTemplate.skill_id == skill_id)
            .where(SkillTemplate.version == version)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, template_id: str) -> Optional[SkillTemplate]:
        """Fetch a skill template by UUID."""
        result = await self.session.execute(
            select(SkillTemplate).where(SkillTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create_template(self, data: dict) -> SkillTemplate:
        """Create a new skill template."""
        template = SkillTemplate(
            skill_id=data["skill_id"],
            name=data["name"],
            domain=data["domain"],
            complexity_score=float(data["complexity_score"]),
            structure=data["structure"],
            version=1,
            is_active=True,
        )
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def list_active_skills(self) -> list[SkillTemplate]:
        """Return all active skill templates (latest version only)."""
        # Get the latest version of each active skill
        result = await self.session.execute(
            select(SkillTemplate)
            .where(SkillTemplate.is_active == True)
            .order_by(SkillTemplate.skill_id, SkillTemplate.version.desc())
            .distinct(SkillTemplate.skill_id)
        )
        return result.scalars().all()

    async def deactivate_previous_versions(self, skill_id: str) -> None:
        """Deactivate all previous versions of a skill."""
        await self.session.execute(
            update(SkillTemplate)
            .where(SkillTemplate.skill_id == skill_id)
            .where(SkillTemplate.is_active == True)
            .values(is_active=False)
        )
        await self.session.commit()

    async def increment_version(
        self, skill_id: str, new_data: dict
    ) -> SkillTemplate:
        """Create a new version of an existing skill template."""
        # Get current active version
        current = await self.get_active_template(skill_id)
        if not current:
            raise ValueError(f"No active template found for skill_id: {skill_id}")

        # Deactivate current version
        await self.deactivate_previous_versions(skill_id)

        # Create new version
        template = SkillTemplate(
            skill_id=skill_id,
            name=new_data.get("name", current.name),
            domain=new_data.get("domain", current.domain),
            complexity_score=float(new_data.get("complexity_score", current.complexity_score)),
            structure=new_data.get("structure", current.structure),
            version=current.version + 1,
            is_active=True,
        )
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template
