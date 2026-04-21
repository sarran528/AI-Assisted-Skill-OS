from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.session.schemas import SessionCompleteRequest, SessionStartRequest
from backend.session.service import (
	complete_session as complete_session_service,
	start_session as start_session_service,
	submit_metrics as submit_metrics_service,
)
from backend.shared.db.session import get_db_session
from backend.shared.db.repositories.roadmap_repository import RoadmapRepository
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/start", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def start_session(
	request: Request,
	payload: SessionStartRequest,
	current_user: dict = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	"""Start a learning session for the user."""
	roadmap_id = payload.roadmap_id
	if roadmap_id is None:
		if payload.skill_id is None:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="roadmap_id_or_skill_id_required")
		roadmap = await RoadmapRepository.get_active(db_session, current_user["user"].id, payload.skill_id)
		if roadmap is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="roadmap_not_found")
		roadmap_id = roadmap.id

	session = await start_session_service(
		db=db_session,
		user_id=current_user["user"].id,
		roadmap_id=roadmap_id,
		phase=payload.phase,
		technique_id=payload.technique_id,
		attempt_number=payload.attempt_number,
	)
	return {"session_id": str(session.id), "status": session.status}


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("120/minute")
async def submit_metrics(
	request: Request,
	payload: dict,
	current_user: dict = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	"""Capture a real-time metrics payload for an active session."""
	if "session_id" not in payload:
		return {"status": "error", "detail": "session_id_required"}

	session_id = payload.get("session_id")
	metrics_payload = dict(payload)
	metrics_payload.pop("session_id", None)

	await submit_metrics_service(db_session, session_id, metrics_payload)
	return {"status": "captured", "session_id": session_id}


@router.post("/complete", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def complete_session(
	request: Request,
	payload: SessionCompleteRequest,
	current_user: dict = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	"""Complete a session and return pass/fail summary."""
	response = await complete_session_service(db_session, payload.session_id, payload.completed_steps)
	return response.model_dump()
