from __future__ import annotations

import structlog

from jevops.workers.celery_app import celery_app

logger = structlog.stdlib.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_review_webhook(self, webhook_url: str, payload: dict, secret: str) -> dict:
    """Send webhook notification when a review is needed."""
    import hashlib
    import hmac
    import json

    import httpx

    body = json.dumps(payload, default=str)
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

    try:
        response = httpx.post(
            webhook_url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-JevOps-Signature": f"sha256={signature}",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("webhook.delivered", url=webhook_url, status=response.status_code)
        return {"status": "delivered", "status_code": response.status_code}
    except httpx.HTTPError as exc:
        logger.warning("webhook.failed", url=webhook_url, error=str(exc))
        raise self.retry(exc=exc) from exc
