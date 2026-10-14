from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jevops.database.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(63), unique=True)

    projects: Mapped[list[Project]] = relationship(back_populates="organization")  # noqa: F821
    api_keys: Mapped[list[APIKey]] = relationship(back_populates="organization")  # noqa: F821
