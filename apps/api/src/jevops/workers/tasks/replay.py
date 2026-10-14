from __future__ import annotations

import structlog

from jevops.workers.celery_app import celery_app

logger = structlog.stdlib.get_logger()


@celery_app.task(bind=True)
def run_replay_task(self, replay_id: str, org_id: str, decision_ids: list[str]) -> dict:
    """Execute a replay run as a background Celery task."""
    import asyncio
    import uuid

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from jevops.config import get_settings
    from jevops.replays.service import ReplayService

    async def _execute():
        settings = get_settings()
        engine = create_async_engine(settings.db.async_url)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            service = ReplayService(session)
            run = await service.execute_replay(
                replay_id=uuid.UUID(replay_id),
                org_id=uuid.UUID(org_id),
                decision_ids=[uuid.UUID(d) for d in decision_ids],
            )
            return {
                "replay_id": str(run.id),
                "status": run.status,
                "agreement_rate": run.agreement_rate,
                "completed": run.completed_decisions,
                "failed": run.failed_decisions,
            }

        await engine.dispose()

    return asyncio.run(_execute())
