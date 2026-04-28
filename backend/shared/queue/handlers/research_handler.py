"""Handler for skill/research.compose.requested event."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.profile_vector import ProfileVector
from backend.shared.db import get_session
from backend.shared.db.repositories.job_repository import JobRepository
from backend.skill.intelligence_service import SkillIntelligenceService

logger = logging.getLogger(__name__)


async def handle_skill_research_compose(
    event_id: str,
    user_id: str,
    skill_id: str,
    profile: dict,
    user_answers: dict | None = None,
    template_constants: dict | None = None,
    serp_aspects: list[str] | None = None,
) -> dict:
    """
    Handle skill research composition event.
    
    Executes:
    1. Fetch user profile and skill template
    2. Run LLM-based research computation (4 LLM calls)
    3. Generate skill research object with feasibility, risk, time modeling
    4. Persist to database
    5. Update job status with result
    """
    session: AsyncSession = get_session()
    job_repo = JobRepository(session)
    
    try:
        # Update job status to running
        await job_repo.update_job_status(event_id, "running")
        
        # Initialize intelligence service
        intelligence_service = SkillIntelligenceService(session)
        
        # Convert profile dict to ProfileVector
        profile_vector = ProfileVector.model_validate(profile)
        
        logger.info("Starting skill research composition", extra={
            "event_id": event_id,
            "user_id": user_id,
            "skill_id": skill_id
        })
        
        # Generate complete skill research object
        research_object = await intelligence_service.generate_skill_research(
            user_id=UUID(user_id),
            skill_id=skill_id,
            profile=profile_vector,
            user_goal=user_answers.get("target_goal") if user_answers else None,
            user_answers=user_answers,
            template_constants=template_constants,
        )
        
        # Result includes feasibility, risk zones, time modeling, modifiers
        result = {
            "skill_id": research_object.skill_id,
            "user_id": str(research_object.user_id),
            "is_feasible": research_object.is_feasible,
            "estimated_weeks": research_object.estimated_weeks,
            "overall_risk": research_object.overall_risk,
            "feasibility": research_object.feasibility.model_dump() if research_object.feasibility else {},
            "risk_zones": research_object.risk_zones.model_dump() if research_object.risk_zones else {},
            "time_model": research_object.time_model.model_dump() if research_object.time_model else {},
            "skill_modifiers": research_object.skill_modifiers.model_dump() if research_object.skill_modifiers else {},
            "phases": research_object.phases,
            "techniques": research_object.techniques,
            "prerequisites": research_object.prerequisites,
            "estimated_total_hours": research_object.estimated_total_hours,
            "user_answers": research_object.user_answers,
        }
        
        await job_repo.update_job_status(event_id, "complete", result=result)
        
        logger.info("Skill research composition completed", extra={
            "event_id": event_id,
            "skill_id": skill_id,
            "is_feasible": research_object.is_feasible,
            "estimated_weeks": research_object.estimated_weeks,
            "status": "complete"
        })
        
        return result
        
    except Exception as e:
        logger.error("Skill research composition handler failed", exc_info=True, extra={
            "event_id": event_id,
            "skill_id": skill_id,
            "user_id": user_id,
            "error": str(e)
        })
        await job_repo.update_job_status(event_id, "failed", error=str(e))
        raise
