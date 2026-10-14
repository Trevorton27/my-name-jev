from __future__ import annotations

import enum
import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jevops.database.base import Base, TenantMixin, TimestampMixin


class Disposition(str, enum.Enum):
    ALLOW = "allow"
    RETRY = "retry"
    HUMAN_REVIEW = "human_review"
    BLOCK = "block"


class Decision(Base, TenantMixin, TimestampMixin):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"))
    policy_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("policy_versions.id"))
    action_type: Mapped[str] = mapped_column(String(255))
    action: Mapped[dict] = mapped_column(JSONB, default=dict)
    objective: Mapped[str | None] = mapped_column(Text)
    state: Mapped[dict] = mapped_column(JSONB, default=dict)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    disposition: Mapped[str] = mapped_column(String(20))
    final_disposition: Mapped[str | None] = mapped_column(String(20))
    policy_trace: Mapped[dict] = mapped_column(JSONB, default=dict)
    provider_latency_ms: Mapped[float | None] = mapped_column(Float)
    provider_model: Mapped[str | None] = mapped_column(String(63))
    environment: Mapped[str] = mapped_column(String(20), default="test")
    mode: Mapped[str] = mapped_column(String(10), default="observe")
    correlation_id: Mapped[str | None] = mapped_column(String(255), index=True)

    judgments: Mapped[list[Judgment]] = relationship(back_populates="decision")


class Judgment(Base, TimestampMixin):
    __tablename__ = "judgments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decisions.id"), index=True)
    question_key: Mapped[str] = mapped_column(String(255))
    question_type: Mapped[str] = mapped_column(String(20))  # noul, choice, score
    value: Mapped[dict] = mapped_column(JSONB)
    confidence: Mapped[float | None] = mapped_column(Float)
    raw_response: Mapped[dict] = mapped_column(JSONB, default=dict)

    decision: Mapped[Decision] = relationship(back_populates="judgments")
