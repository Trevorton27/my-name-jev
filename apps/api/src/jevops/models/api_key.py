from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jevops.database.base import Base, TenantMixin, TimestampMixin


class APIKey(Base, TenantMixin, TimestampMixin):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    prefix: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    key_hash: Mapped[str] = mapped_column(String(64))
    environment: Mapped[str] = mapped_column(String(10), default="test")  # "live" or "test"
    is_active: Mapped[bool] = mapped_column(default=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    organization: Mapped[Organization] = relationship(back_populates="api_keys")  # noqa: F821
