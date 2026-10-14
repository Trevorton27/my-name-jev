from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jevops.database.base import Base, TenantMixin, TimestampMixin


class Policy(Base, TenantMixin, TimestampMixin):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(63))
    description: Mapped[str | None] = mapped_column(Text)
    action_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    is_active: Mapped[bool] = mapped_column(default=True)
    active_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("policy_versions.id"))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    versions: Mapped[list[PolicyVersion]] = relationship(
        back_populates="policy",
        foreign_keys="PolicyVersion.policy_id",
    )


class PolicyVersion(Base, TimestampMixin):
    __tablename__ = "policy_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(default=1)
    policy_yaml: Mapped[str] = mapped_column(Text)
    parsed_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policies.id"))

    policy: Mapped[Policy] = relationship(
        back_populates="versions",
        foreign_keys=[policy_id],
    )
