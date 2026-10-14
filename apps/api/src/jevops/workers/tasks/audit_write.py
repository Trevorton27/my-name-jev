from __future__ import annotations

import structlog

from jevops.workers.celery_app import celery_app

logger = structlog.stdlib.get_logger()


@celery_app.task
def write_audit_event(event_data: dict) -> dict:
    """Async audit event write for non-critical audit logging."""
    logger.info("audit.async_write", event_type=event_data.get("event_type"))
    # In production, this would write to the database
    # For now, log it
    return {"status": "recorded", "event_type": event_data.get("event_type")}
