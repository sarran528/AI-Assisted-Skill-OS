"""Handler for skill/discover.requested event."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db import get_session
from backend.shared.db.models import Job
from backend.shared.db.repositories.job_repository import JobRepository
from backend.skill.service import SkillTemplateService
from backend.skill.template_pipeline import SkillTemplatePipeline

logger = logging.getLogger(__name__)


async def handle_skill_discovery(
    event_id: str,
    skill_name: str,
    domain: str,
    complexity_score: float,
    requested_by_user_id: str,
    serp_aspects: list[str],
) -> dict:
    """
    Handle skill discovery event.
    
    Executes:
    1. SERP search for each of 8 aspects
    2. Extract and aggregate results
    3. LLM pass 1: concept extraction
    4. LLM pass 2: template construction
    5. Persist skill template to database
    6. Update job status with result
    """
    session: AsyncSession = get_session()
    job_repo = JobRepository(session)
    
    try:
        # Update job status to running
        await job_repo.update_job_status(event_id, "running")
        
        # Initialize skill template service
        skill_service = SkillTemplateService(session)
        pipeline = SkillTemplatePipeline()
        
        # Execute SERP searches for all aspects
        logger.info(f"Starting SERP searches for skill: {skill_name}", extra={
            "event_id": event_id,
            "skill_name": skill_name,
            "aspect_count": len(serp_aspects)
        })
        
        serp_results = {}
        for aspect in serp_aspects:
            try:
                results = await pipeline.execute_serp_search(
                    skill_name=skill_name,
                    domain=domain,
                    aspect=aspect
                )
                serp_results[aspect] = results
                logger.debug(f"SERP search completed for aspect: {aspect}", extra={
                    "event_id": event_id,
                    "aspect": aspect,
                    "result_count": len(results) if results else 0
                })
            except Exception as e:
                logger.error(f"SERP search failed for aspect: {aspect}", exc_info=True, extra={
                    "event_id": event_id,
                    "aspect": aspect
                })
                serp_results[aspect] = []
        
        # Aggregate SERP results
        aggregated_content = await pipeline.aggregate_serp_results(serp_results)
        
        # LLM Pass 1: Concept extraction
        logger.info("Starting LLM Pass 1: concept extraction", extra={"event_id": event_id})
        concepts = await pipeline.extract_concepts(
            skill_name=skill_name,
            aggregated_content=aggregated_content
        )
        
        # LLM Pass 2: Template construction
        logger.info("Starting LLM Pass 2: template construction", extra={"event_id": event_id})
        template_structure = await pipeline.construct_template(
            skill_name=skill_name,
            concepts=concepts,
            complexity_score=complexity_score
        )
        
        # Create skill template
        skill_id = pipeline.to_skill_id(skill_name)
        template = await skill_service.create_skill_template(
            payload={
                "skill_id": skill_id,
                "name": skill_name,
                "domain": domain,
                "structure": template_structure,
                "complexity_score": complexity_score,
                "created_by": requested_by_user_id,
            }
        )
        
        # Update job with result
        result = {
            "skill_id": skill_id,
            "skill_name": skill_name,
            "domain": domain,
            "complexity_score": complexity_score,
            "template_version": getattr(template, "version", 1),
            "serp_queries_executed": len(serp_results),
            "serp_aspects": serp_aspects,
        }
        
        await job_repo.update_job_status(event_id, "complete", result=result)
        
        logger.info("Skill discovery completed successfully", extra={
            "event_id": event_id,
            "skill_id": skill_id,
            "status": "complete"
        })
        
        return result
        
    except Exception as e:
        logger.error("Skill discovery handler failed", exc_info=True, extra={
            "event_id": event_id,
            "skill_name": skill_name,
            "error": str(e)
        })
        await job_repo.update_job_status(event_id, "failed", error=str(e))
        raise
