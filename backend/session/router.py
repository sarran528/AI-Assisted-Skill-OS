from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.session.schemas import (
	SessionCompleteRequest,
	SessionCompleteResponse,
	SessionMetricsRequest,
	SessionStartRequest,
	SessionStartResponse,
	SessionStatusResponse,
)
from backend.session.service import complete_session, get_session_status, start_session, submit_metrics
from backend.shared.db.session import get_db_session

router = APIRouter()


@router.post("/start", response_model=SessionStartResponse)
async def start_session_route(
	payload: SessionStartRequest,
	db: AsyncSession = Depends(get_db_session),
	current_user: dict = Depends(get_current_user),
) -> SessionStartResponse:
	session = await start_session(
		db=db,
		user_id=current_user["user"].id,
		roadmap_id=payload.roadmap_id,
		phase=payload.phase,
		technique_id=payload.technique_id,
		attempt_number=payload.attempt_number,
	)
	return SessionStartResponse(session_id=session.id, status=session.status)


@router.post("/{session_id}/metrics", status_code=status.HTTP_204_NO_CONTENT)
async def submit_session_metrics_route(
	session_id: UUID,
	payload: SessionMetricsRequest,
	db: AsyncSession = Depends(get_db_session),
	_current_user: dict = Depends(get_current_user),
	) -> Response:
	await submit_metrics(db=db, session_id=session_id, metrics_payload=payload.metrics)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{session_id}/complete", response_model=SessionCompleteResponse)
async def complete_session_route(
	session_id: UUID,
	payload: SessionCompleteRequest,
	db: AsyncSession = Depends(get_db_session),
	_current_user: dict = Depends(get_current_user),
) -> SessionCompleteResponse:
	return await complete_session(db=db, session_id=session_id, completed_steps=payload.completed_steps)


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session_status_route(
	session_id: UUID,
	db: AsyncSession = Depends(get_db_session),
	_current_user: dict = Depends(get_current_user),
) -> SessionStatusResponse:
	session = await get_session_status(db=db, session_id=session_id)
	if session is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	return SessionStatusResponse(
		session_id=session.id,
		status=session.status,
		phase=session.phase,
		technique_id=session.technique_id,
		attempt_number=int(session.attempt_number),
		started_at=session.started_at,
		ended_at=session.ended_at,
	)
