from celery import Celery

from backend.shared.config import settings

celery_app = Celery(
    "skillos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.shared.queue.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    worker_concurrency=4,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_time_limit=120,
    task_soft_time_limit=90,
    worker_max_tasks_per_child=50,
)

# Import schedules after app creation so beat settings are registered.
from backend.shared.queue import beat_schedule  # noqa: E402,F401
