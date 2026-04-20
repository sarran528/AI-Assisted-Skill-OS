import uuid

from fastapi import APIRouter, Request
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from backend.auth.dependencies import get_current_user
from backend.shared.audit import log_audit_event
from backend.shared.db.models import Job
from backend.shared.db.session import get_db_session
from backend.shared.queue.tasks import generate_roadmap_task
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_roadmap(
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> dict:
    job_id = uuid.uuid4()
    await db_session.execute(insert(Job).values(id=job_id, status="queued"))
    await db_session.commit()

    generate_roadmap_task.delay(str(job_id))
    user_id = str(current_user["user"].id)
    await log_audit_event(
        db_session,
        user_id=user_id,
        action="roadmap.generated",
        entity_type="job",
        entity_id=str(job_id),
        ip_address=request.client.host if request.client else "",
    )
    return {"job_id": str(job_id), "status": "queued"}


@router.get("/jobs/{job_id}")
async def get_job_status(
	job_id: str,
	db_session: AsyncSession = Depends(get_db_session),
) -> dict:
	try:
		job_uuid = uuid.UUID(job_id)
	except ValueError:
		return {"job_id": job_id, "status": "invalid"}

	result = await db_session.execute(select(Job).where(Job.id == job_uuid))
	job = result.scalar_one_or_none()
	if not job:
		return {"job_id": job_id, "status": "not_found"}
	return {"job_id": job_id, "status": job.status}
