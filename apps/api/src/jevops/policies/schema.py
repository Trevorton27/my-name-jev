from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QuestionDef(BaseModel):
    type: str  # noul, choice, score
    instructions: str
    criteria: dict[str, str] | list[str] | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("noul", "choice", "score"):
            raise ValueError(f"Invalid question type: {v}")
        return v


class RuleCondition(BaseModel):
    all: list[str] | None = None
    any: list[str] | None = None

    # Single expression shorthand
    expr: str | None = Field(None, alias="when")


class Rule(BaseModel):
    name: str
    when: str | RuleCondition
    then: str  # allow, retry, human_review, block
    priority: int = 100
    reason: str = ""

    @field_validator("then")
    @classmethod
    def validate_disposition(cls, v: str) -> str:
        valid = {"allow", "retry", "human_review", "block"}
        if v not in valid:
            raise ValueError(f"Invalid disposition: {v}. Must be one of {valid}")
        return v


class EnvironmentThreshold(BaseModel):
    key: str
    production: float | None = None
    staging: float | None = None
    development: float | None = None


class ErrorCosts(BaseModel):
    false_allow: float = 1.0
    false_block: float = 1.0


class PolicyConfig(BaseModel):
    name: str
    version: str = "1"
    description: str = ""
    action_types: list[str] = Field(default_factory=list)
    questions: dict[str, QuestionDef] = Field(default_factory=dict)
    rules: list[Rule] = Field(default_factory=list)
    default: str = "human_review"
    environment_thresholds: list[EnvironmentThreshold] = Field(default_factory=list)
    error_costs: ErrorCosts = Field(default_factory=ErrorCosts)

    @field_validator("default")
    @classmethod
    def validate_default(cls, v: str) -> str:
        valid = {"allow", "retry", "human_review", "block"}
        if v not in valid:
            raise ValueError(f"Invalid default disposition: {v}")
        return v
