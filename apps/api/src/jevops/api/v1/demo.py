from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.database.seed import seed_demo_data
from jevops.database.session import get_db

router = APIRouter(prefix="/demo", tags=["demo"])


def require_demo_reset_token(
    request: Request,
    token: str | None = Header(default=None, alias="X-Demo-Reset-Token"),
) -> None:
    """Reset wipes every org, so it is off unless a reset token is configured and supplied."""
    expected = request.app.state.settings.security.demo_reset_token
    if not expected:
        raise HTTPException(status_code=403, detail="Demo reset is disabled")
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Invalid demo reset token")


@router.post("/reset", dependencies=[Depends(require_demo_reset_token)])
async def reset_demo(db: AsyncSession = Depends(get_db)):
    """Clear and re-seed demo data."""
    # Delete all data in reverse dependency order
    from jevops.models import (
        Agent,
        APIKey,
        AuditEvent,
        Decision,
        DecisionOutcome,
        Judgment,
        Organization,
        Policy,
        PolicyVersion,
        Project,
        ReplayRun,
        Review,
    )

    from sqlalchemy import delete, update

    # Break circular FK: policies.active_version_id -> policy_versions
    await db.execute(update(Policy).values(active_version_id=None))
    await db.flush()

    for model in [
        AuditEvent,
        DecisionOutcome,
        Judgment,
        Review,
        ReplayRun,
        Decision,
        PolicyVersion,
        Policy,
        Agent,
        APIKey,
        Project,
        Organization,
    ]:
        await db.execute(delete(model))
    await db.commit()

    result = await seed_demo_data(db)
    return {"status": "reset", "api_key": result["api_key"], "details": result}
