from celery import Celery

from backend.shared.config import settings

celery_app = Celery(
    "skillos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_acks_late=True,
    worker_concurrency=4,
    task_time_limit=120,
    task_soft_time_limit=110,
    task_default_retry_delay=10,
    task_max_retries=3,
)
