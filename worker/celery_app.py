from celery import Celery
from api.config import get_settings

settings = get_settings()
celery_app = Celery("amrisk", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "daily-brief": {
            "task": "worker.tasks.daily_brief_task",
            "schedule": crontab(hour=settings.DAILY_CRON_HOUR, minute=settings.DAILY_CRON_MINUTE),
        },
    },
)

from celery.schedules import crontab
