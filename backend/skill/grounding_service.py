"""Service layer for skill grounding operations."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.profile_vector import ProfileVector
from backend.shared.audit import log_audit_event
from backend.shared.db.repositories.grounding_repository import GroundingRepository
from backend.shared.db.repositories.skill_template_repository import (
    SkillTemplateRepository,
)
from backend.shared.errors import BusinessError
from backend.skill.grounding import compute_baseline_with_declarative
from backend.skill.grounding_schemas import GroundingProbeResponses, BaselineSkillStateResponse


class GroundingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GroundingRepository(session)
        self.skill_repo = SkillTemplateRepository(session)

    async def submit_grounding(
        self,
        user_id: UUID,
        skill_id: str,
        responses: GroundingProbeResponses,
        profile: ProfileVector,
        ip_address: str = "127.0.0.1",
    ) -> BaselineSkillStateResponse:
        """Submit grounding probe responses for a skill.
        
        Args:
            user_id: User ID
            skill_id: Skill being grounded
            responses: Grounding probe responses
            profile: User's ProfileVector for actual_level
            ip_address: IP address for audit log
            
        Returns:
            BaselineSkillStateResponse with computed state
            
        Raises:
            BusinessError if skill not found or responses invalid
        """
        # Verify skill exists
        skill = await self.skill_repo.get_active_template(skill_id)
        if not skill:
            raise BusinessError(
                code="skill_not_found",
                message=f"Skill template not found: {skill_id}",
            )

        # Get correct answer indices from skill template
        skill_structure = skill.structure
        grounding_probes = skill_structure.get("grounding_probes", {})
        familiarity_probes = grounding_probes.get("familiarity", [])
        
        # Extract correct indices from probes
        correct_indices = [
            probe.get("correct_index", 0)
            for probe in familiarity_probes
        ]

        # Prepare responses
        exposure_responses = responses.recognition.items if responses.recognition else []
        familiarity_responses = responses.familiarity.answers if responses.familiarity else []
        confidence_response = responses.confidence.level if responses.confidence else 3  # Default middle value

        # Compute baseline state
        baseline_state = compute_baseline_with_declarative(
            exposure_responses=exposure_responses,
            familiarity_responses=familiarity_responses,
            familiarity_correct_indices=correct_indices,
            confidence_response=confidence_response,
            profile=profile,
            skill_id=skill_id,
            user_id=user_id,
        )

        # Persist baseline state
        raw_responses = {
            "exposure": exposure_responses,
            "familiarity": familiarity_responses,
            "confidence": confidence_response,
        }

        baseline_record = await self.repo.create_baseline(
            user_id=user_id,
            skill_id=skill_id,
            exposure_score=baseline_state.exposure_score,
            declarative_score=baseline_state.declarative_score,
            confidence_score=baseline_state.confidence_score,
            perceived_level=baseline_state.perceived_level,
            actual_level=baseline_state.actual_level,
            confidence_bias=baseline_state.confidence_bias,
            raw_responses=raw_responses,
        )

        # Write audit log
        await log_audit_event(
            user_id=user_id,
            action="skill.grounding_completed",
            entity_type="baseline_skill_state",
            entity_id=str(baseline_record.id),
            ip_address=ip_address,
            metadata={
                "skill_id": skill_id,
                "confidence_bias": float(baseline_state.confidence_bias),
            },
        )

        return BaselineSkillStateResponse(
            id=baseline_record.id,
            skill_id=baseline_record.skill_id,
            user_id=baseline_record.user_id,
            exposure_score=float(baseline_record.exposure_score),
            declarative_score=float(baseline_record.declarative_score),
            confidence_score=float(baseline_record.confidence_score),
            perceived_level=float(baseline_record.perceived_level),
            actual_level=float(baseline_record.actual_level),
            confidence_bias=float(baseline_record.confidence_bias),
            created_at=baseline_record.created_at,
        )
