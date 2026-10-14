from __future__ import annotations

import enum
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jevops.database.base import Base, TenantMixin, TimestampMixin


class ReplayStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReplayRun(Base, TenantMixin, TimestampMixin):
    __tablename__ = "replay_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=ReplayStatus.PENDING.value)
    policy_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("policy_versions.id"))
    provider_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    total_decisions: Mapped[int] = mapped_column(Integer, default=0)
    completed_decisions: Mapped[int] = mapped_column(Integer, default=0)
    failed_decisions: Mapped[int] = mapped_column(Integer, default=0)
    agreement_rate: Mapped[float | None] = mapped_column(Float)
    results_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
