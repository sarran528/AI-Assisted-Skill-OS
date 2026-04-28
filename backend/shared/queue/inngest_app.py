import inngest
from backend.shared.config import settings
from backend.shared.queue.handlers import (
    handle_skill_discovery,
    handle_skill_research_compose,
    handle_roadmap_generation,
)

# Initialize Inngest client
inngest_client = inngest.Inngest(
    app_id="skillos_backend",
    event_key=settings.inngest_event_key,
)

# Define Inngest functions wrapping the handlers
@inngest_client.create_function(
    fn_id="skill-discovery",
    trigger=inngest.TriggerEvent(event="skill/discover.requested"),
)
async def discovery_function(ctx: inngest.Context, step: inngest.Step):
    data = ctx.event.data
    return await handle_skill_discovery(
        event_id=ctx.event.id,
        skill_name=data["skill_name"],
        domain=data["domain"],
        complexity_score=data["complexity_score"],
        requested_by_user_id=data["requested_by_user_id"],
        serp_aspects=data["serp_aspects"],
    )

@inngest_client.create_function(
    fn_id="skill-research-compose",
    trigger=inngest.TriggerEvent(event="skill/research.compose.requested"),
)
async def research_compose_function(ctx: inngest.Context, step: inngest.Step):
    return await handle_skill_research_compose(
        event_id=ctx.event.id,
        **ctx.event.data
    )

@inngest_client.create_function(
    fn_id="roadmap-generation",
    trigger=inngest.TriggerEvent(event="roadmap/generate.requested"),
)
async def roadmap_generation_function(ctx: inngest.Context, step: inngest.Step):
    return await handle_roadmap_generation(
        event_id=ctx.event.id,
        user_id=ctx.event.data["user_id"],
        skill_id=ctx.event.data["skill_id"],
    )

# List of all Inngest functions to be served
inngest_functions = [
    discovery_function,
    research_compose_function,
    roadmap_generation_function,
]
