from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.queue.tasks import validate_checkpoint_task
from backend.validation.schemas import CheckpointValidateRequest
from backend.shared.db.models import CheckpointState
from backend.shared.db.session import get_db_session

router = APIRouter()


@router.post("/validate")
async def enqueue_checkpoint_validation(payload: CheckpointValidateRequest) -> dict:
	task = validate_checkpoint_task.delay(str(payload.session_id), payload.checkpoint_id)
	return {"job_id": task.id}


@router.get("/{roadmap_id}")
async def list_checkpoints(
	roadmap_id: UUID,
	db_session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
	result = await db_session.execute(
		select(CheckpointState).where(CheckpointState.roadmap_id == roadmap_id)
	)
	items = result.scalars().all()
	return [
		{
			"checkpoint_id": item.checkpoint_id,
			"status": item.status,
			"phase": item.phase_slug,
		}
		for item in items
	]
