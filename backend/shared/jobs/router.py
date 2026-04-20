from fastapi import APIRouter

from backend.shared.queue.celery_app import celery_app

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: str) -> dict:
    result = celery_app.AsyncResult(job_id)
    payload = result.result if isinstance(result.result, dict) else None
    return {"status": result.state, "result": payload}
