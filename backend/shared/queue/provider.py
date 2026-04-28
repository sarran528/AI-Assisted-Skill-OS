from __future__ import annotations

import logging
import uuid

import httpx

from backend.shared.config import settings

logger = logging.getLogger(__name__)


async def _enqueue_inngest_event(name: str, data: dict) -> str:
    if not settings.inngest_event_key:
        raise ValueError("INNGEST_EVENT_KEY is required when USE_INNGEST_QUEUE=true")

    event_url = f"{settings.inngest_event_base_url.rstrip('/')}/{settings.inngest_event_key}"
    event_id = str(uuid.uuid4())
    payload = {
        "id": event_id,
        "name": name,
        "data": data,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(event_url, json=payload)
        response.raise_for_status()

    return event_id


async def queue_roadmap_generation(user_id: str, skill_id: str) -> tuple[str, str]:
    """Queue roadmap generation using Inngest.

    Returns:
        tuple[str, str]: (provider, job_id)
    """
    if not settings.use_inngest_queue:
        raise ValueError("USE_INNGEST_QUEUE must be true. Celery queue has been removed.")

    event_id = await _enqueue_inngest_event(
        name="roadmap/generate.requested",
        data={"user_id": user_id, "skill_id": skill_id},
    )
    logger.info("Queued roadmap generation with Inngest", extra={"event_id": event_id, "user_id": user_id, "skill_id": skill_id})
    return ("inngest", event_id)


async def queue_skill_discovery(skill_name: str, domain: str, complexity_score: float, requested_by_user_id: str) -> tuple[str, str]:
    if not settings.use_inngest_queue:
        raise ValueError("USE_INNGEST_QUEUE must be true. Celery queue has been removed.")

    serp_aspects = [
        "skill_definition_and_scope",
        "foundational_subskills",
        "tooling_and_prerequisites",
        "common_beginner_mistakes",
        "learning_path_milestones",
        "portfolio_project_ideas",
        "market_demand_and_roles",
        "practice_resources_and_communities",
    ]

    event_id = await _enqueue_inngest_event(
        name="skill/discover.requested",
        data={
            "skill_name": skill_name,
            "domain": domain,
            "complexity_score": complexity_score,
            "requested_by_user_id": requested_by_user_id,
            "search_provider": settings.search_provider,
            "serp_aspects": serp_aspects,
        },
    )
    logger.info("Queued skill discovery with Inngest", extra={"event_id": event_id, "skill_name": skill_name, "requested_by_user_id": requested_by_user_id})
    return ("inngest", event_id)


async def queue_skill_research_compose(data: dict) -> tuple[str, str]:
    if not settings.use_inngest_queue:
        raise ValueError("USE_INNGEST_QUEUE must be true. Celery queue has been removed.")

    event_id = await _enqueue_inngest_event(
        name="skill/research.compose.requested",
        data=data,
    )
    logger.info("Queued skill research compose with Inngest", extra={"event_id": event_id, "skill_id": data.get("skill_id"), "user_id": data.get("user_id")})
    return ("inngest", event_id)


async def queue_named_event(name: str, data: dict) -> tuple[str, str]:
    if not settings.use_inngest_queue:
        raise ValueError("USE_INNGEST_QUEUE must be true. Celery queue has been removed.")

    event_id = await _enqueue_inngest_event(name=name, data=data)
    logger.info("Queued named Inngest event", extra={"event_id": event_id, "event_name": name})
    return ("inngest", event_id)
