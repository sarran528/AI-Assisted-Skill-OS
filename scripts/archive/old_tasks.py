from backend.shared.queue.celery_app import celery_app


@celery_app.task
def placeholder_task() -> str:
    return "ok"


@celery_app.task
def generate_roadmap_task(job_id: str) -> str:
    return job_id
