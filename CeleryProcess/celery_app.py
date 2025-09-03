from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

celery_app = Celery(
    "ingestion_processor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["CeleryProcess.task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_pool="prefork",
    worker_concurrency=2,
    timezone="UTC",
    enable_utc=True,

    task_routes={
        "tasks.process_ingestion": {"queue": "ingestion"},
        "tasks.ai_processing_task": {"queue": "ai_processing"},
    },

    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    result_expires=3600,

    beat_schedule={
        "periodic-ingestion": {
            "task": "tasks.process_ingestion",
            "schedule": crontab(minute="*/10"),  # every 10 minutes
        },
    },
)

if __name__ == "__main__":
    celery_app.start()
