from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class CreateReplayRequest(BaseModel):
    name: str
    description: str | None = None
    policy_version_id: uuid.UUID | None = None
    provider_config: dict[str, Any] = Field(default_factory=dict)
    decision_ids: list[uuid.UUID] = Field(default_factory=list)


class ReplayResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: str
    total_decisions: int
    completed_decisions: int
    failed_decisions: int
    agreement_rate: float | None
    results_summary: dict[str, Any]
    created_at: str | None = None

    model_config = {"from_attributes": True}
