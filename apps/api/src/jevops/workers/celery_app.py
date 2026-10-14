from __future__ import annotations

import os

from celery import Celery


def create_celery_app() -> Celery:
    broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    app = Celery("jevops", broker=broker, backend=backend)
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_default_retry_delay=60,
        task_max_retries=3,
    )
    app.autodiscover_tasks(["jevops.workers.tasks"])
    return app


celery_app = create_celery_app()
