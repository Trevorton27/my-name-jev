from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from jevops.jev.types import QuestionType


class QuestionInput(BaseModel):
    type: QuestionType
    instructions: str
    criteria: dict[str, str] | list[str] | None = None


class EvaluateRequest(BaseModel):
    agent_id: uuid.UUID
    action_type: str
    action: dict[str, Any] = Field(default_factory=dict)
    objective: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    questions: dict[str, QuestionInput] | None = None
    environment: str = "test"
    idempotency_key: str | None = None


class JudgmentResponse(BaseModel):
    question_key: str
    question_type: str
    value: Any
    probabilities: dict[str, float] | None = None
    confidence: float | None = None


class DecisionResponse(BaseModel):
    id: uuid.UUID
    disposition: str
    final_disposition: str | None = None
    action_type: str
    mode: str
    environment: str
    judgments: list[JudgmentResponse] = []
    policy_trace: dict[str, Any] = {}
    provider_latency_ms: float | None = None
    provider_model: str | None = None
    correlation_id: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class OutcomeRequest(BaseModel):
    ground_truth_label: str | None = None
    outcome_data: dict[str, Any] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    feedback: str
