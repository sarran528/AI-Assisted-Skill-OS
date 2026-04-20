from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.roadmap.generator import verify_roadmap_integrity
from backend.roadmap.schemas import (
    GeneratedRoadmap,
    RoadmapGenerateRequest,
    RoadmapGenerateResponse,
    RoadmapResponse,
    RoadmapVerifyResponse,
)
from backend.shared.db.repositories.roadmap_repository import RoadmapRepository
from backend.shared.db.session import get_db_session
from backend.shared.queue.tasks import generate_roadmap_task
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, response_model=RoadmapGenerateResponse)
@limiter.limit("5/minute")
async def generate_roadmap(
    request: Request,
    payload: RoadmapGenerateRequest,
    current_user: dict = Depends(get_current_user),
) -> RoadmapGenerateResponse:
    _ = request
    task = generate_roadmap_task.delay(str(current_user["user"].id), payload.skill_id)
    return RoadmapGenerateResponse(job_id=task.id, status="queued")


@router.get("/{user_id}", response_model=RoadmapResponse)
async def get_active_roadmap(
    user_id: UUID,
    skill_id: str,
    db_session: AsyncSession = Depends(get_db_session),
) -> RoadmapResponse:
    roadmap = await RoadmapRepository.get_active(db_session, user_id, skill_id)
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active roadmap found")
    return RoadmapResponse(
        roadmap_id=roadmap.id,
        skill_id=roadmap.skill_id,
        user_id=roadmap.user_id,
        structure=roadmap.structure,
        fingerprint=roadmap.fingerprint,
        status=roadmap.status,
    )


@router.get("/{roadmap_id}/verify", response_model=RoadmapVerifyResponse)
async def verify_roadmap(
    roadmap_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
) -> RoadmapVerifyResponse:
    model = await RoadmapRepository.get_by_id(db_session, roadmap_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    parsed = GeneratedRoadmap.model_validate(model.structure)
    is_valid = verify_roadmap_integrity(parsed)
    return RoadmapVerifyResponse(valid=is_valid, fingerprint=model.fingerprint)
