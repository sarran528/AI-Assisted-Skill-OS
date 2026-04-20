"""
Business logic for skill template management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from jsonschema import ValidationError

from backend.shared.db.repositories.skill_template_repository import (
    SkillTemplateRepository,
)
from backend.shared.errors import BusinessError
from backend.skill.template_schema import validate_template_structure
from backend.skill.schemas import SkillTemplateCreate, SkillTemplateResponse
from backend.shared.db.models import SkillTemplate


class SkillTemplateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SkillTemplateRepository(session)

    async def create_skill_template(
        self, payload: SkillTemplateCreate
    ) -> SkillTemplate:
        """
        Create a new skill template or increment version if exists.
        Validates structure before creation.
        """
        # Validate structure
        try:
            validate_template_structure(payload.structure)
        except ValidationError as e:
            raise BusinessError(
                code="invalid_template_structure",
                message=f"Invalid skill template structure: {e.message}",
                context={"field": e.json_path},
            )

        # Check if skill already exists
        existing = await self.repo.get_active_template(payload.skill_id)
        
        if existing:
            # Create new version
            template = await self.repo.increment_version(
                payload.skill_id,
                {
                    "name": payload.name,
                    "domain": payload.domain,
                    "complexity_score": payload.complexity_score,
                    "structure": payload.structure,
                },
            )
        else:
            # Create new template
            template = await self.repo.create_template(
                {
                    "skill_id": payload.skill_id,
                    "name": payload.name,
                    "domain": payload.domain,
                    "complexity_score": payload.complexity_score,
                    "structure": payload.structure,
                }
            )

        return template

    async def get_skill(self, skill_id: str) -> SkillTemplate:
        """Get active skill template by skill_id."""
        template = await self.repo.get_active_template(skill_id)
        if not template:
            raise BusinessError(
                code="skill_not_found",
                message=f"Skill template not found: {skill_id}",
            )
        return template

    async def list_skills(self) -> list[SkillTemplate]:
        """List all active skill templates."""
        return await self.repo.list_active_skills()
