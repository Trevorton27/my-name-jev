from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.auth.middleware import AuthContext, require_api_key
from jevops.database.session import get_db
from jevops.replays.schemas import CreateReplayRequest, ReplayResponse
from jevops.replays.service import ReplayService

router = APIRouter(prefix="/replays", tags=["replays"])


def _to_response(run) -> ReplayResponse:
    return ReplayResponse(
        id=run.id,
        name=run.name,
        description=run.description,
        status=run.status.value if hasattr(run.status, "value") else run.status,
        total_decisions=run.total_decisions,
        completed_decisions=run.completed_decisions,
        failed_decisions=run.failed_decisions,
        agreement_rate=run.agreement_rate,
        results_summary=run.results_summary,
        created_at=run.created_at.isoformat() if run.created_at else None,
    )


@router.post("", response_model=ReplayResponse)
async def create_replay(
    body: CreateReplayRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReplayService(db)
    run = await service.create_replay(
        org_id=auth.org_id,
        name=body.name,
        description=body.description,
        policy_version_id=body.policy_version_id,
        provider_config=body.provider_config,
    )
    return _to_response(run)


@router.get("", response_model=list[ReplayResponse])
async def list_replays(
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReplayService(db)
    runs = await service.list_replays(auth.org_id)
    return [_to_response(r) for r in runs]


@router.get("/{replay_id}", response_model=ReplayResponse)
async def get_replay(
    replay_id: uuid.UUID,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReplayService(db)
    run = await service.get_replay(replay_id, auth.org_id)
    if not run:
        raise HTTPException(status_code=404, detail="Replay not found")
    return _to_response(run)


@router.post("/{replay_id}/execute")
async def execute_replay(
    replay_id: uuid.UUID,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReplayService(db)
    try:
        run = await service.execute_replay(replay_id, auth.org_id, decision_ids=[])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return _to_response(run)
