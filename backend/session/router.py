from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.session.schemas import (
	SessionCompleteRequest,
	SessionMetricsRequest,
	SessionStartRequest,
)
from backend.session.service import complete_session, get_session_status, start_session, submit_metrics
from backend.shared.db.session import get_db_session

router = APIRouter()


@router.post("/start")
async def start_session_route(
	payload: SessionStartRequest,
	db_session: AsyncSession = Depends(get_db_session),
	current_user: dict = Depends(get_current_user),
) -> dict:
	session_id = await start_session(
		db_session,
		current_user["user"].id,
		payload.roadmap_id,
		payload.phase,
		payload.technique_id,
	)
	return {"session_id": str(session_id)}


@router.post("/metrics")
async def submit_metrics_route(
	payload: SessionMetricsRequest,
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	await submit_metrics(db_session, payload.session_id, payload.metrics)
	return {"acknowledged": True}


@router.post("/complete")
async def complete_session_route(
	payload: SessionCompleteRequest,
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	result = await complete_session(db_session, None, payload.session_id, payload.completed_steps)
	return {
		"passed": result.passed,
		"failure_reason": result.failure_reason,
		"metric_details": result.metric_details,
	}


@router.get("/{session_id}")
async def get_session_route(
	session_id: UUID,
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	return await get_session_status(db_session, session_id)
