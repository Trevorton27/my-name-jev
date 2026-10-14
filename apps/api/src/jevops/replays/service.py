from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from jevops.models.decision import Decision
from jevops.models.replay import ReplayRun, ReplayStatus
from jevops.policies.schema import PolicyConfig
from jevops.replays.engine import replay_decision


class ReplayService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_replay(
        self,
        org_id: uuid.UUID,
        name: str,
        description: str | None = None,
        policy_version_id: uuid.UUID | None = None,
        provider_config: dict[str, Any] | None = None,
    ) -> ReplayRun:
        run = ReplayRun(
            org_id=org_id,
            name=name,
            description=description,
            policy_version_id=policy_version_id,
            provider_config=provider_config or {},
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_replay(self, replay_id: uuid.UUID, org_id: uuid.UUID) -> ReplayRun | None:
        result = await self.session.execute(
            select(ReplayRun).where(ReplayRun.id == replay_id, ReplayRun.org_id == org_id)
        )
        return result.scalar_one_or_none()

    async def list_replays(self, org_id: uuid.UUID) -> list[ReplayRun]:
        result = await self.session.execute(
            select(ReplayRun).where(ReplayRun.org_id == org_id).order_by(ReplayRun.created_at.desc())
        )
        return list(result.scalars().all())

    async def execute_replay(
        self,
        replay_id: uuid.UUID,
        org_id: uuid.UUID,
        decision_ids: list[uuid.UUID],
        policy_config: PolicyConfig | None = None,
    ) -> ReplayRun:
        run = await self.get_replay(replay_id, org_id)
        if not run:
            raise ValueError("Replay not found")

        run.status = ReplayStatus.RUNNING.value
        run.total_decisions = len(decision_ids)
        await self.session.flush()

        agreements = 0
        failures = 0
        disposition_changes: dict[str, int] = {}

        for did in decision_ids:
            result = await self.session.execute(
                select(Decision)
                .where(Decision.id == did, Decision.org_id == org_id)
                .options(selectinload(Decision.judgments))
            )
            decision = result.scalar_one_or_none()
            if not decision:
                failures += 1
                continue

            decision_data = {
                "disposition": decision.disposition,
                "action_type": decision.action_type,
            }
            judgments_data = [
                {
                    "question_key": j.question_key,
                    "question_type": j.question_type,
                    "value": j.value,
                    "confidence": j.confidence,
                }
                for j in decision.judgments
            ]

            try:
                replay_result = replay_decision(decision_data, judgments_data, policy_config)
                if replay_result.changed:
                    key = f"{replay_result.original_disposition}->{replay_result.new_disposition}"
                    disposition_changes[key] = disposition_changes.get(key, 0) + 1
                else:
                    agreements += 1
                run.completed_decisions += 1
            except Exception:
                failures += 1

        run.failed_decisions = failures
        completed = run.completed_decisions
        run.agreement_rate = agreements / max(completed, 1)
        run.results_summary = {
            "agreements": agreements,
            "changes": disposition_changes,
            "failures": failures,
        }
        run.status = ReplayStatus.COMPLETED.value
        await self.session.flush()
        return run
