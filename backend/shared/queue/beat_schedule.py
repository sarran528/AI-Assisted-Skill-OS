from celery.schedules import crontab

from backend.shared.queue.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "backend.shared.queue.tasks.cleanup_expired_tokens_task",
        "schedule": crontab(hour=2, minute=0),
    }
}
