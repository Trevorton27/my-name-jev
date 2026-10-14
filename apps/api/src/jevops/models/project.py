from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jevops.database.base import Base, TenantMixin, TimestampMixin


class ProjectMode(str, enum.Enum):
    OBSERVE = "observe"
    ENFORCE = "enforce"


class Project(Base, TenantMixin, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(63))
    mode: Mapped[str] = mapped_column(String(10), default=ProjectMode.OBSERVE.value)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    organization: Mapped[Organization] = relationship(back_populates="projects")  # noqa: F821
    agents: Mapped[list[Agent]] = relationship(back_populates="project")  # noqa: F821
