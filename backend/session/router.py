from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status

from backend.auth.dependencies import get_current_user
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/start", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def start_session(
	request: Request,
	payload: dict,
	current_user: dict = Depends(get_current_user),
) -> dict:
	"""Start a learning session for the user."""
	return {
		"session_id": str(uuid4()),
		"status": "active",
		"skill_id": payload.get("skill_id"),
		"phase": payload.get("phase"),
		"technique_id": payload.get("technique_id"),
		"started_at": datetime.now(timezone.utc).isoformat(),
		"user_id": str(current_user["user"].id),
	}


@router.post("/metrics", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("120/minute")
async def submit_metrics(
	request: Request,
	payload: dict,
	current_user: dict = Depends(get_current_user),
) -> dict:
	"""Capture a real-time metrics payload for an active session."""
	return {
		"status": "captured",
		"session_id": payload.get("session_id"),
		"received_at": datetime.now(timezone.utc).isoformat(),
		"user_id": str(current_user["user"].id),
	}


@router.post("/complete", status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def complete_session(
	request: Request,
	payload: dict,
	current_user: dict = Depends(get_current_user),
) -> dict:
	"""Complete a session and return pass/fail summary."""
	completed_steps = payload.get("completed_steps", [])
	passed = len(completed_steps) >= 4
	return {
		"session_id": payload.get("session_id"),
		"passed": passed,
		"tip_pending": not passed,
		"completed_steps": completed_steps,
		"completed_at": datetime.now(timezone.utc).isoformat(),
		"user_id": str(current_user["user"].id),
	}
