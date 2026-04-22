from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.shared.rate_limit import limiter
from backend.shared.db.session import get_db_session
from backend.shared.db.repositories.tip_repository import TipRepository
from backend.support.doubt_service import answer_doubt
from backend.support.resource_service import get_resources
from backend.support.schemas import (
    DoubtAskRequest,
    DoubtResponseModel,
    ResourceResponseModel,
    TipPendingResponse,
    TipResponseModel,
)


router = APIRouter()


@router.get("/resources", response_model=ResourceResponseModel)
async def get_resources_route(
    skill_id: str = Query(..., min_length=1),
    phase: str = Query(..., min_length=1),
    technique_id: str | None = Query(default=None),
    user_query: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> ResourceResponseModel:
    query = user_query or technique_id
    response = await get_resources(
        db=db,
        skill_id=skill_id,
        phase=phase,
        user_query=query,
        current_user=current_user,
    )
    return ResourceResponseModel(
        skill_id=response.skill_id,
        phase=response.phase,
        resources=response.resources,
        query_used=response.query_used,
    )


@router.post("/doubt/ask", response_model=DoubtResponseModel)
@limiter.limit("10/minute")
async def ask_doubt_route(
    request: Request,
    payload: DoubtAskRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> DoubtResponseModel:
    del request
    response = await answer_doubt(
        db=db,
        user_id=current_user["user"].id,
        session_id=payload.session_id,
        user_question=payload.user_query,
        current_user=current_user,
    )
    return DoubtResponseModel(
        explanation=response.answer,
        sources_used=response.chunks_used,
    )


@router.get("/tip/{session_id}", response_model=TipResponseModel | TipPendingResponse)
async def get_tip_route(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> TipResponseModel | TipPendingResponse:
    del current_user
    repo = TipRepository(db)
    tip = await repo.get_latest_for_session(session_id)
    if tip is None:
        return TipPendingResponse(tip_pending=True, session_id=session_id)

    return TipResponseModel(
        tip=tip.tip,
        trigger_reason=tip.failure_type,
    )
