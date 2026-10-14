from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.database.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id: uuid.UUID, org_id: uuid.UUID) -> T | None:
        result = await self.session.execute(
            select(self.model).where(
                self.model.id == id,  # type: ignore[attr-defined]
                self.model.org_id == org_id,  # type: ignore[attr-defined]
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, org_id: uuid.UUID, limit: int = 100, offset: int = 0) -> list[T]:
        result = await self.session.execute(
            select(self.model)
            .where(self.model.org_id == org_id)  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
            .order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
        )
        return list(result.scalars().all())

    async def create(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        return instance
