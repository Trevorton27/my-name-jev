from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    agent_id: str
    action_type: str
    action: dict[str, Any] = Field(default_factory=dict)
    objective: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    questions: dict[str, dict[str, Any]] | None = None
    environment: str = "test"
    idempotency_key: str | None = None


class JudgmentResponse(BaseModel):
    question_key: str
    question_type: str
    value: Any
    probabilities: dict[str, float] | None = None
    confidence: float | None = None


class DecisionResponse(BaseModel):
    id: str
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

    @property
    def is_allowed(self) -> bool:
        return self.disposition == "allow"

    @property
    def needs_review(self) -> bool:
        return self.disposition == "human_review"

    @property
    def is_blocked(self) -> bool:
        return self.disposition == "block"


class OutcomeRequest(BaseModel):
    ground_truth_label: str | None = None
    outcome_data: dict[str, Any] = Field(default_factory=dict)


class ReviewResponse(BaseModel):
    id: str
    decision_id: str
    status: str
    reviewer: str | None = None
    reason: str | None = None
    notes: str | None = None
    created_at: str | None = None
