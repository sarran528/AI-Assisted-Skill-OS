from fastapi import APIRouter

from backend.shared.queue.tasks import validate_checkpoint_task
from backend.validation.schemas import CheckpointValidateRequest

router = APIRouter()


@router.post("/checkpoint/validate")
async def enqueue_checkpoint_validation(payload: CheckpointValidateRequest) -> dict:
	task = validate_checkpoint_task.delay(str(payload.session_id), payload.checkpoint_id)
	return {"job_id": task.id}
