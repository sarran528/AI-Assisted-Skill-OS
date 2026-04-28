from fastapi import APIRouter
from backend.shared.config import settings

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: str) -> dict:
    if settings.use_inngest_queue:
        return {
            "status": "queued",
            "provider": "inngest",
            "job_id": job_id,
            "result": None,
            "note": "Track execution in Inngest dashboard or webhook sink until status backend is integrated.",
        }

    return {
        "status": "disabled",
        "provider": "none",
        "job_id": job_id,
        "result": None,
        "note": "No queue provider configured.",
    }
