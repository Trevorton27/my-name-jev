from __future__ import annotations

import uuid

from sqlalchemy import select

from jevops.database.repositories.base import BaseRepository
from jevops.models.policy import Policy, PolicyVersion


class PolicyRepository(BaseRepository[Policy]):
    model = Policy

    async def find_by_action_type(self, action_type: str, org_id: uuid.UUID) -> list[Policy]:
        result = await self.session.execute(
            select(Policy).where(
                Policy.org_id == org_id,
                Policy.is_active == True,  # noqa: E712
                Policy.action_types.any(action_type),
            )
        )
        return list(result.scalars().all())

    async def get_active_version(self, policy_id: uuid.UUID) -> PolicyVersion | None:
        policy = await self.session.get(Policy, policy_id)
        if not policy or not policy.active_version_id:
            return None
        return await self.session.get(PolicyVersion, policy.active_version_id)

    async def create_version(self, version: PolicyVersion) -> PolicyVersion:
        self.session.add(version)
        await self.session.flush()
        return version
