from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jevops.database.base import Base, TenantMixin, TimestampMixin


class DecisionOutcome(Base, TenantMixin, TimestampMixin):
    __tablename__ = "decision_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decisions.id"), unique=True, index=True)
    ground_truth_label: Mapped[str | None] = mapped_column(String(20))
    outcome_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    feedback: Mapped[str | None] = mapped_column(Text)
