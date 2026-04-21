from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.auth.dependencies import get_current_user
from backend.orchestration.orchestrator import transition_session
from backend.shared.rate_limit import limiter
from backend.session.execution import SessionMetrics, compute_session_result, validate_protocol_adherence

router = APIRouter()


@router.post("/start", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def start_session(
	request: Request,
	payload: dict,
	current_user: dict = Depends(get_current_user),
) -> dict:
	"""Start a learning session for the user."""
	current_status = payload.get("current_status", "pending")
	if not transition_session(current_status, "active"):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_start_session_transition")

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
	session_status = payload.get("session_status", "active")
	if session_status != "active":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="metrics_only_allowed_for_active_session")

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
	required_steps = payload.get("required_steps", ["1", "2", "3", "4"])
	current_status = payload.get("current_status", "active")

	if not transition_session(current_status, "completed") and not transition_session(current_status, "failed"):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_session_status_transition")

	adherence_ok, missing_steps = validate_protocol_adherence(completed_steps, required_steps)
	metrics_input = payload.get("metrics", {})
	step_completion_rate = len(completed_steps) / max(len(required_steps), 1)
	accuracy = metrics_input.get("accuracy", payload.get("accuracy"))
	time_taken_seconds = metrics_input.get("elapsed_seconds", payload.get("elapsed_seconds"))
	error_count = metrics_input.get("errors", payload.get("errors"))
	retry_count = metrics_input.get("retry", payload.get("retry", 0))
	error_tolerance_threshold = float(payload.get("error_tolerance_threshold", 0.7))

	if accuracy is not None:
		accuracy = float(accuracy)
	if time_taken_seconds is not None:
		time_taken_seconds = float(time_taken_seconds)
	if error_count is not None:
		error_count = int(error_count)
	retry_count = int(retry_count)

	metrics = SessionMetrics(
		accuracy_pct=accuracy,
		time_taken_seconds=time_taken_seconds,
		error_count=error_count,
		step_completion_rate=step_completion_rate,
		retry_count=retry_count,
		raw_signals={
			"required_steps": required_steps,
			"completed_steps": completed_steps,
			"missing_steps": missing_steps,
			"metrics": metrics_input,
		},
	)

	result = compute_session_result(
		metrics=metrics,
		error_tolerance_threshold=error_tolerance_threshold,
		adherence_ok=adherence_ok,
	)
	target_status = "completed" if result.passed else "failed"
	if not transition_session(current_status, target_status):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_target_session_status")

	return {
		"session_id": payload.get("session_id"),
		"status": target_status,
		"passed": result.passed,
		"tip_pending": not result.passed,
		"failure_reason": result.failure_reason,
		"metric_details": result.metric_details,
		"completed_steps": completed_steps,
		"required_steps": required_steps,
		"missing_steps": missing_steps,
		"completed_at": datetime.now(timezone.utc).isoformat(),
		"user_id": str(current_user["user"].id),
	}
