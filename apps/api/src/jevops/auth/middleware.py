from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.auth.api_key import parse_api_key, verify_api_key
from jevops.database.session import get_db
from jevops.models.api_key import APIKey

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthContext:
    def __init__(self, org_id: uuid.UUID, api_key_id: uuid.UUID, environment: str) -> None:
        self.org_id = org_id
        self.api_key_id = api_key_id
        self.environment = environment


async def require_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
    key: str | None = Security(api_key_header),
) -> AuthContext:
    if not key:
        raise HTTPException(status_code=401, detail="Missing API key")

    parsed = parse_api_key(key)
    if not parsed:
        raise HTTPException(status_code=401, detail="Invalid API key format")

    prefix, secret = parsed
    settings = request.app.state.settings

    result = await db.execute(
        select(APIKey).where(APIKey.prefix == prefix, APIKey.is_active == True)  # noqa: E712
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not verify_api_key(secret, settings.security.api_key_pepper, api_key.key_hash):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return AuthContext(
        org_id=api_key.organization_id,
        api_key_id=api_key.id,
        environment=api_key.environment,
    )
