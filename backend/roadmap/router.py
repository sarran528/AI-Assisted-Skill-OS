from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import AuthContext, get_current_user
from backend.roadmap.generator import verify_roadmap_integrity
from backend.roadmap.schemas import (
    GeneratedRoadmap,
    RoadmapGenerateRequest,
    RoadmapGenerateResponse,
    RoadmapVerifyResponse,
)
from backend.shared.models import APIModel
from backend.shared.db.repositories.roadmap_repository import RoadmapRepository
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter
from backend.shared.queue.celery_app import celery_app

router = APIRouter()


class FlowPhaseSchema(APIModel):
    phase_slug: str
    competencies: list[str]
    techniques: list[str]
    checkpoints: list[str]
    estimated_hours: float
    status: str


class FlowRoadmapResponse(APIModel):
    id: UUID
    skill_id: str
    profile_version: int
    phases: list[FlowPhaseSchema]
    status: str
    created_at: str | None


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, response_model=RoadmapGenerateResponse)
@limiter.limit("5/minute")
async def generate_roadmap(
    request: Request,
    payload: RoadmapGenerateRequest,
    current_user: AuthContext = Depends(get_current_user),
) -> RoadmapGenerateResponse:
    from backend.shared.queue.tasks import generate_roadmap_task
    _ = request
    task = generate_roadmap_task.delay(str(current_user.user.id), payload.skill_id)
    return RoadmapGenerateResponse(job_id=task.id, status="queued")


@router.get("/{user_id}", response_model=FlowRoadmapResponse)
async def get_active_roadmap(
    user_id: UUID,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> FlowRoadmapResponse:
    if str(user_id) != str(current_user.user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    roadmap = await RoadmapRepository.get_active_for_user(db_session, user_id)
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active roadmap found")

    generated = GeneratedRoadmap.model_validate(roadmap.structure)
    phases = [
        FlowPhaseSchema(
            phase_slug=phase_slug,
            competencies=list(phase.competencies),
            techniques=[technique.technique_id for technique in phase.techniques],
            checkpoints=[checkpoint.checkpoint_id for checkpoint in phase.checkpoints],
            estimated_hours=float(phase.estimated_weeks) * 5.0,
            status=phase.status,
        )
        for phase_slug, phase in generated.phases.items()
    ]

    return FlowRoadmapResponse(
        id=roadmap.id,
        skill_id=roadmap.skill_id,
        profile_version=generated.profile_version,
        phases=phases,
        status=roadmap.status,
        created_at=roadmap.created_at.isoformat() if roadmap.created_at else None,
    )


@router.get("/{user_id}/status")
async def get_roadmap_status(
    user_id: UUID,
    job_id: str | None = None,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    if str(user_id) != str(current_user.user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    roadmap = await RoadmapRepository.get_active_for_user(db_session, user_id)
    if roadmap is not None:
        return {"status": "completed", "job_id": job_id}

    if job_id:
        result = celery_app.AsyncResult(job_id)
        if result.state in {"PENDING", "STARTED"}:
            return {"status": "queued", "job_id": job_id}
        if result.state == "SUCCESS":
            return {"status": "completed", "job_id": job_id}
        return {"status": "failed", "job_id": job_id}

    return {"status": "queued", "job_id": job_id}


@router.patch("/{roadmap_id}/abandon")
async def abandon_roadmap(
    roadmap_id: UUID,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    roadmap = await RoadmapRepository.get_by_id(db_session, roadmap_id)
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    if str(roadmap.user_id) != str(current_user.user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    await RoadmapRepository.update_status(db_session, roadmap_id, "abandoned")
    return {"status": "abandoned"}


@router.get("/{roadmap_id}/verify", response_model=RoadmapVerifyResponse)
async def verify_roadmap(
    roadmap_id: UUID,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> RoadmapVerifyResponse:
    model = await RoadmapRepository.get_by_id(db_session, roadmap_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    if str(model.user_id) != str(current_user.user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    parsed = GeneratedRoadmap.model_validate(model.structure)
    is_valid = verify_roadmap_integrity(parsed)
    return RoadmapVerifyResponse(valid=is_valid, fingerprint=model.fingerprint)
