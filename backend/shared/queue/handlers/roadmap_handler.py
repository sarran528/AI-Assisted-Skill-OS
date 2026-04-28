"""Handler for roadmap/generate.requested event."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.roadmap.service import create_roadmap
from backend.shared.db import get_session
from backend.shared.db.repositories.job_repository import JobRepository
from backend.shared.db.repositories.roadmap_repository import RoadmapRepository

logger = logging.getLogger(__name__)


async def handle_roadmap_generation(
    event_id: str,
    user_id: str,
    skill_id: str,
    skill_research: dict | None = None,
    profile: dict | None = None,
) -> dict:
    """
    Handle roadmap generation event.
    
    Executes:
    1. Fetch or use provided skill research
    2. Generate roadmap phases, checkpoints, and milestones
    3. Verify roadmap integrity
    4. Persist to database
    5. Update job status with result
    """
    session: AsyncSession = get_session()
    job_repo = JobRepository(session)
    roadmap_repo = RoadmapRepository(session)
    
    try:
        # Update job status to running
        await job_repo.update_job_status(event_id, "running")
        
        logger.info("Starting roadmap generation", extra={
            "event_id": event_id,
            "user_id": user_id,
            "skill_id": skill_id
        })
        
        # Build and persist the roadmap using the real roadmap service helper.
        roadmap = await create_roadmap(session, UUID(user_id), skill_id)
        persisted_roadmap = await RoadmapRepository.get_active(session, UUID(user_id), skill_id)
        
        result = {
            "skill_id": skill_id,
            "user_id": user_id,
            "roadmap_id": getattr(persisted_roadmap, "id", None),
            "total_phases": len(roadmap.phases) if hasattr(roadmap, "phases") else 0,
            "total_weeks": roadmap.total_weeks if hasattr(roadmap, "total_weeks") else 0,
            "total_hours": roadmap.total_hours if hasattr(roadmap, "total_hours") else 0,
            "status": "generated",
        }
        
        await job_repo.update_job_status(event_id, "complete", result=result)
        
        logger.info("Roadmap generation completed", extra={
            "event_id": event_id,
            "skill_id": skill_id,
            "total_phases": result["total_phases"],
            "status": "complete"
        })
        
        return result
        
    except Exception as e:
        logger.error("Roadmap generation handler failed", exc_info=True, extra={
            "event_id": event_id,
            "skill_id": skill_id,
            "user_id": user_id,
            "error": str(e)
        })
        await job_repo.update_job_status(event_id, "failed", error=str(e))
        raise
