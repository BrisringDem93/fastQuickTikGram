from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "fastquicktikgram",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.video_tasks",
        "app.workers.hook_tasks",
        "app.workers.publish_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=900,        # 15 min hard limit
    # Retry policy defaults
    task_max_retries=3,
    task_default_retry_delay=60,  # seconds
)

# ------------------------------------------------------------------
# Celery Beat periodic tasks
# ------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    "check-scheduled-jobs": {
        "task": "app.workers.publish_tasks.scheduler_beat_task",
        "schedule": crontab(minute="*/1"),  # every minute
        "options": {"expires": 50},
    },
}
