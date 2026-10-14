from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


class TypedQuestion(BaseModel):
    type: QuestionType
    instructions: str
    criteria: dict[str, str] | list[str] | None = None


class JudgmentResult(BaseModel):
    question_key: str
    question_type: QuestionType
    value: Any  # float for noul/score, str for choice
    probabilities: dict[str, float] | None = None
    confidence: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ProviderEvaluation(BaseModel):
    judgments: list[JudgmentResult]
    model: str = "unknown"
    latency_ms: float = 0.0
    raw_response: dict[str, Any] = Field(default_factory=dict)
