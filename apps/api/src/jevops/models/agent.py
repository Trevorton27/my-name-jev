from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jevops.database.base import Base, TenantMixin, TimestampMixin


class Agent(Base, TenantMixin, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(63))
    description: Mapped[str | None] = mapped_column(String(1000))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    project: Mapped[Project] = relationship(back_populates="agents")  # noqa: F821
