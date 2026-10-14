from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from jevops.database.repositories.base import BaseRepository
from jevops.models.decision import Decision, Judgment


class DecisionRepository(BaseRepository[Decision]):
    model = Decision

    async def list_all(self, org_id: uuid.UUID, limit: int = 100, offset: int = 0) -> list[Decision]:
        result = await self.session.execute(
            select(Decision)
            .where(Decision.org_id == org_id)
            .options(selectinload(Decision.judgments))
            .order_by(Decision.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_idempotency_key(self, idempotency_key: str, org_id: uuid.UUID) -> Decision | None:
        result = await self.session.execute(
            select(Decision)
            .where(Decision.idempotency_key == idempotency_key, Decision.org_id == org_id)
            .options(selectinload(Decision.judgments))
        )
        return result.scalar_one_or_none()

    async def get_with_judgments(self, id: uuid.UUID, org_id: uuid.UUID) -> Decision | None:
        result = await self.session.execute(
            select(Decision)
            .where(Decision.id == id, Decision.org_id == org_id)
            .options(selectinload(Decision.judgments))
        )
        return result.scalar_one_or_none()

    async def add_judgment(self, judgment: Judgment) -> Judgment:
        self.session.add(judgment)
        await self.session.flush()
        return judgment


class DecisionOutcomeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, outcome: DecisionOutcome) -> DecisionOutcome:  # noqa: F821
        self.session.add(outcome)
        await self.session.flush()
        return outcome
