from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Job
from backend.shared.db.session import get_db_session
from backend.shared.queue.tasks import validate_checkpoint_task
from backend.validation.engine import validate_checkpoint
from backend.validation.schemas import CheckpointValidateRequest, CheckpointValidateResponse

router = APIRouter()


@router.post("/checkpoint/validate", response_model=CheckpointValidateResponse, status_code=status.HTTP_200_OK)
async def run_checkpoint_validation(
	payload: CheckpointValidateRequest,
	db_session: AsyncSession = Depends(get_db_session),
) -> CheckpointValidateResponse:
	passed, reason = await validate_checkpoint(
		db_session=db_session,
		session_id=UUID(payload.session_id),
		checkpoint_id=payload.checkpoint_id,
		checkpoint_status=payload.checkpoint_status,
		evidence_type=payload.evidence_type,
		numeric_actual=payload.numeric_actual,
		numeric_threshold=payload.numeric_threshold,
		steps_completed=payload.steps_completed,
		required_steps=payload.required_steps,
		retry_count=payload.retry_count,
		max_retries=payload.max_retries,
	)
	return CheckpointValidateResponse(
		passed=passed,
		reason=reason,
		session_id=payload.session_id,
		checkpoint_id=payload.checkpoint_id,
	)


@router.post("/checkpoint/validate/async", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_checkpoint_validation(
	payload: CheckpointValidateRequest,
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	job_id = uuid.uuid4()
	await db_session.execute(insert(Job).values(id=job_id, status="queued"))
	await db_session.commit()

	validate_checkpoint_task.delay(
		payload.session_id,
		payload.checkpoint_id,
		payload.checkpoint_status,
		str(job_id),
	)

	return {
		"job_id": str(job_id),
		"status": "queued",
		"session_id": payload.session_id,
		"checkpoint_id": payload.checkpoint_id,
	}
