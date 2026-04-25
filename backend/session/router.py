from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import AuthContext, get_current_user
from backend.session.schemas import (
	SessionCompleteRequest,
	SessionListItem,
	SessionListResponse,
	SessionMetricsRequest,
	SessionStartRequest,
	SessionStatusResponse,
)
from backend.session.service import (
	complete_session as complete_session_service,
	get_session_status as get_session_status_service,
	list_recent_sessions as list_recent_sessions_service,
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
	current_user: AuthContext = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	"""Start a learning session for the user."""
	roadmap_id = payload.roadmap_id
	if roadmap_id is None:
		if payload.skill_id is None:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="roadmap_id_or_skill_id_required")
		roadmap = await RoadmapRepository.get_active(db_session, current_user.user.id, payload.skill_id)
		if roadmap is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="roadmap_not_found")
		roadmap_id = roadmap.id

	session = await start_session_service(
		db=db_session,
		user_id=current_user.user.id,
		roadmap_id=roadmap_id,
		phase=payload.phase,
		technique_id=payload.technique_id,
		attempt_number=payload.attempt_number,
	)
	return {"session_id": str(session.id), "status": session.status}


@router.get("/recent", response_model=SessionListResponse)
@limiter.limit("30/minute")
async def list_recent_sessions(
	request: Request,
	limit: int = 5,
	current_user: AuthContext = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> SessionListResponse:
	limit = min(max(limit, 1), 20)
	sessions = await list_recent_sessions_service(db_session, current_user.user.id, limit)
	items: list[SessionListItem] = []
	for session in sessions:
		metrics = session.metrics_captured or {}
		score_value = metrics.get("accuracy")
		items.append(
			SessionListItem(
				session_id=session.id,
				status=session.status,
				phase=session.phase,
				score=float(score_value) if score_value is not None else None,
				created_at=session.created_at,
			)
		)
	return SessionListResponse(items=items)


@router.get("/{session_id}", response_model=SessionStatusResponse)
@limiter.limit("60/minute")
async def get_session(
	request: Request,
	session_id: UUID,
	current_user: AuthContext = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> SessionStatusResponse:
	_ = request
	session = await get_session_status_service(db_session, session_id, current_user.user.id)
	if session is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")

	return SessionStatusResponse(
		session_id=session.id,
		status=session.status,
		phase=session.phase,
		technique_id=session.technique_id,
		attempt_number=int(session.attempt_number),
		started_at=session.started_at,
		ended_at=session.ended_at,
	)


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("120/minute")
async def submit_metrics(
	request: Request,
	payload: SessionMetricsRequest,
	current_user: AuthContext = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	"""Capture a real-time metrics payload for an active session."""
	_ = request
	await submit_metrics_service(db_session, payload.session_id, current_user.user.id, payload.metrics)
	return {"status": "captured", "session_id": payload.session_id}


@router.post("/complete", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def complete_session(
	request: Request,
	payload: SessionCompleteRequest,
	current_user: AuthContext = Depends(get_current_user),
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	"""Complete a session and return pass/fail summary."""
	_ = request
	response = await complete_session_service(db_session, payload.session_id, current_user.user.id, payload.completed_steps)
	return response.model_dump()
