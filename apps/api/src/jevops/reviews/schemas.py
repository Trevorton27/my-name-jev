from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel


class ReviewResponse(BaseModel):
    id: uuid.UUID
    decision_id: uuid.UUID
    status: str
    reviewer: str | None = None
    reason: str | None = None
    corrected_judgments: dict[str, Any] | None = None
    notes: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    reviewer: str
    reason: str | None = None
    notes: str | None = None


class RejectRequest(BaseModel):
    reviewer: str
    reason: str
    notes: str | None = None


class RetryRequest(BaseModel):
    reviewer: str
    reason: str
    notes: str | None = None


class CorrectJudgmentsRequest(BaseModel):
    reviewer: str
    corrected_judgments: dict[str, Any]
    notes: str | None = None
