"""Service layer for skill intelligence engine."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.profile_vector import ProfileVector
from backend.shared.audit import log_audit_event
from backend.shared.db.repositories.grounding_repository import GroundingRepository
from backend.shared.db.repositories.skill_research_repository import SkillResearchRepository
from backend.shared.db.repositories.skill_template_repository import SkillTemplateRepository
from backend.shared.errors import BusinessError
from backend.skill.intelligence import SkillResearchObject, compute_skill_research

logger = logging.getLogger(__name__)


class SkillIntelligenceService:
    """Orchestrate skill intelligence computation and persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.skill_template_repo = SkillTemplateRepository(session)
        self.grounding_repo = GroundingRepository(session)

    async def generate_skill_research(
        self,
        user_id: UUID,
        skill_id: str,
        profile: ProfileVector,
        ip_address: str = "unknown",
    ) -> SkillResearchObject:
        """
        Generate complete skill research object via four LLM calls.

        Workflow:
        1. Validate skill exists and is active
        2. Fetch latest baseline state (grounding probes must exist)
        3. Call compute_skill_research with all four LLM calls
        4. Persist result to database
        5. Log audit event
        6. Return SkillResearchObject

        Args:
            user_id: User generating research
            skill_id: Target skill
            profile: User's ProfileVector
            ip_address: Caller IP for audit logging

        Returns:
            Assembled SkillResearchObject

        Raises:
            BusinessError: If skill not found or grounding_required
            SystemError: If LLM calls fail unrecoverably
        """
        # Validate skill exists and is active
        skill_template = await self.skill_template_repo.get_active_template(skill_id)
        if not skill_template:
            raise BusinessError("skill_not_found")

        # Fetch latest baseline state (proves grounding was completed)
        baseline_state = await self.grounding_repo.get_latest_baseline(user_id, skill_id)
        if not baseline_state:
            raise BusinessError("grounding_required")

        # Run four sequential LLM calls
        research_object = await compute_skill_research(profile, baseline_state, skill_template)

        # Persist to database
        await SkillResearchRepository.create(self.session, research_object)

        # Log audit event
        await log_audit_event(
            session=self.session,
            user_id=user_id,
            event_type="skill.research_generated",
            metadata={
                "skill_id": skill_id,
                "is_feasible": research_object.is_feasible,
                "estimated_weeks": research_object.estimated_weeks,
                "overall_risk": research_object.overall_risk,
            },
            ip_address=ip_address,
        )

        logger.info(
            f"Generated skill research for user {user_id} skill {skill_id}: "
            f"feasible={research_object.is_feasible}, weeks={research_object.estimated_weeks}"
        )

        return research_object
