from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from jevops.database.repositories.policy_repo import PolicyRepository
from jevops.models.policy import Policy, PolicyVersion
from jevops.policies.engine import PolicyEngine, PolicyResult
from jevops.policies.loader import load_policy_yaml
from jevops.policies.schema import PolicyConfig


class PolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PolicyRepository(session)
        self.engine = PolicyEngine()

    async def create_policy(
        self,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        name: str,
        slug: str,
        policy_yaml: str,
        action_types: list[str] | None = None,
        description: str | None = None,
    ) -> Policy:
        config = load_policy_yaml(policy_yaml)

        policy = Policy(
            org_id=org_id,
            project_id=project_id,
            name=name,
            slug=slug,
            description=description or config.description,
            action_types=action_types or config.action_types,
        )
        policy = await self.repo.create(policy)

        version = PolicyVersion(
            policy_id=policy.id,
            version=1,
            policy_yaml=policy_yaml,
            parsed_config=config.model_dump(),
        )
        version = await self.repo.create_version(version)

        policy.active_version_id = version.id
        await self.session.flush()

        return policy

    async def create_version(self, policy_id: uuid.UUID, org_id: uuid.UUID, policy_yaml: str) -> PolicyVersion:
        policy = await self.repo.get_by_id(policy_id, org_id)
        if not policy:
            raise ValueError("Policy not found")

        config = load_policy_yaml(policy_yaml)

        # Get latest version number
        from sqlalchemy import func, select

        result = await self.session.execute(
            select(func.max(PolicyVersion.version)).where(PolicyVersion.policy_id == policy_id)
        )
        max_ver = result.scalar() or 0

        version = PolicyVersion(
            policy_id=policy_id,
            version=max_ver + 1,
            policy_yaml=policy_yaml,
            parsed_config=config.model_dump(),
        )
        return await self.repo.create_version(version)

    async def activate_version(self, policy_id: uuid.UUID, version_id: uuid.UUID, org_id: uuid.UUID) -> Policy:
        policy = await self.repo.get_by_id(policy_id, org_id)
        if not policy:
            raise ValueError("Policy not found")
        policy.active_version_id = version_id
        await self.session.flush()
        return policy

    async def get_active_config(self, policy_id: uuid.UUID) -> PolicyConfig | None:
        version = await self.repo.get_active_version(policy_id)
        if not version:
            return None
        return load_policy_yaml(version.policy_yaml)

    def evaluate(self, config: PolicyConfig, namespace: dict[str, Any]) -> PolicyResult:
        return self.engine.evaluate(config, namespace)

    def simulate(self, policy_yaml: str, namespace: dict[str, Any]) -> dict[str, Any]:
        config = load_policy_yaml(policy_yaml)
        result = self.engine.evaluate(config, namespace)
        return result.to_dict()
