from __future__ import annotations

import uuid

from pydantic import BaseModel


class WebhookConfig(BaseModel):
    id: uuid.UUID | None = None
    url: str
    secret: str
    events: list[str] = ["review.needed"]
    is_active: bool = True
