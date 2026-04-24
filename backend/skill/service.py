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
from backend.skill.schemas import SkillTemplateCreate, SkillTemplateUpdate
from backend.shared.db.models import SkillTemplate
from backend.skill.template_pipeline import SkillTemplatePipeline, to_legacy_structure, to_skill_id


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

    async def update_skill_template(self, skill_id: str, payload: SkillTemplateUpdate) -> SkillTemplate:
        """Update a skill template by creating a new version."""
        template = await self.repo.get_active_template(skill_id)
        if not template:
            raise BusinessError(
                code="skill_not_found",
                message=f"Skill template not found: {skill_id}",
            )

        if payload.structure is not None:
            try:
                validate_template_structure(payload.structure)
            except ValidationError as e:
                raise BusinessError(
                    code="invalid_template_structure",
                    message=f"Invalid skill template structure: {e.message}",
                    context={"field": e.json_path},
                )

        new_data = {
            "name": payload.name if payload.name is not None else template.name,
            "domain": template.domain,
            "complexity_score": (
                payload.complexity_score if payload.complexity_score is not None else template.complexity_score
            ),
            "structure": payload.structure if payload.structure is not None else template.structure,
        }

        return await self.repo.increment_version(skill_id, new_data)

    async def list_skills(self) -> list[SkillTemplate]:
        """List all active skill templates."""
        return await self.repo.list_active_skills()

    async def build_template_from_skill_name(
        self,
        *,
        skill_name: str,
        domain: str = "other",
        complexity_score: float = 0.5,
    ) -> tuple[SkillTemplate, str, bool]:
        """
        Build and persist a strict skill template from controlled retrieval pipeline.

        Returns:
            (template, generated_version, created_new_record)
        """
        skill_id = to_skill_id(skill_name)
        existing = await self.repo.get_active_template(skill_id)
        if existing:
            return existing, f"v{existing.version}", False

        pipeline = SkillTemplatePipeline()
        try:
            result = await pipeline.build_with_fallback(skill_name)
        finally:
            await pipeline.close()

        if result is None:
            raise BusinessError(
                code="template_generation_failed",
                message="Failed to generate a valid SkillTemplate from external sources",
            )

        structure = to_legacy_structure(result.template)

        try:
            validate_template_structure(structure)
        except ValidationError as e:
            raise BusinessError(
                code="invalid_template_structure",
                message=f"Generated structure failed validation: {e.message}",
                context={"field": e.json_path},
            )

        template = await self.repo.create_template(
            {
                "skill_id": skill_id,
                "name": skill_name,
                "domain": domain,
                "complexity_score": complexity_score,
                "structure": structure,
            }
        )
        return template, result.version, True
