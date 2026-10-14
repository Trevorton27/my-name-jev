from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.auth.middleware import AuthContext, require_api_key
from jevops.database.session import get_db
from jevops.models.policy import Policy, PolicyVersion
from jevops.policies.loader import PolicyLoadError
from jevops.policies.service import PolicyService

router = APIRouter(prefix="/policies", tags=["policies"])


class CreatePolicyRequest(BaseModel):
    name: str
    slug: str
    project_id: uuid.UUID
    policy_yaml: str
    action_types: list[str] = Field(default_factory=list)
    description: str | None = None


class CreateVersionRequest(BaseModel):
    policy_yaml: str


class ActivateVersionRequest(BaseModel):
    version_id: uuid.UUID


class SimulateRequest(BaseModel):
    policy_yaml: str
    namespace: dict[str, Any]


class PolicyResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    action_types: list[str]
    is_active: bool
    active_version_id: uuid.UUID | None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class PolicyVersionResponse(BaseModel):
    id: uuid.UUID
    version: int
    policy_yaml: str
    created_at: str | None = None

    model_config = {"from_attributes": True}


@router.post("", response_model=PolicyResponse)
async def create_policy(
    body: CreatePolicyRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = PolicyService(db)
    try:
        policy = await service.create_policy(
            org_id=auth.org_id,
            project_id=body.project_id,
            name=body.name,
            slug=body.slug,
            policy_yaml=body.policy_yaml,
            action_types=body.action_types,
            description=body.description,
        )
    except PolicyLoadError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return PolicyResponse(
        id=policy.id,
        name=policy.name,
        slug=policy.slug,
        description=policy.description,
        action_types=policy.action_types,
        is_active=policy.is_active,
        active_version_id=policy.active_version_id,
        created_at=policy.created_at.isoformat() if policy.created_at else None,
    )


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Policy).where(Policy.org_id == auth.org_id).order_by(Policy.created_at.desc()))
    policies = result.scalars().all()
    return [
        PolicyResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            action_types=p.action_types,
            is_active=p.is_active,
            active_version_id=p.active_version_id,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in policies
    ]


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    repo = PolicyService(db).repo
    policy = await repo.get_by_id(policy_id, auth.org_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyResponse(
        id=policy.id,
        name=policy.name,
        slug=policy.slug,
        description=policy.description,
        action_types=policy.action_types,
        is_active=policy.is_active,
        active_version_id=policy.active_version_id,
        created_at=policy.created_at.isoformat() if policy.created_at else None,
    )


@router.post("/{policy_id}/versions", response_model=PolicyVersionResponse)
async def create_version(
    policy_id: uuid.UUID,
    body: CreateVersionRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = PolicyService(db)
    try:
        version = await service.create_version(policy_id, auth.org_id, body.policy_yaml)
    except (ValueError, PolicyLoadError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return PolicyVersionResponse(
        id=version.id,
        version=version.version,
        policy_yaml=version.policy_yaml,
        created_at=version.created_at.isoformat() if version.created_at else None,
    )


@router.get("/{policy_id}/versions", response_model=list[PolicyVersionResponse])
async def list_versions(
    policy_id: uuid.UUID,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PolicyVersion).where(PolicyVersion.policy_id == policy_id).order_by(PolicyVersion.version.desc())
    )
    versions = result.scalars().all()
    return [
        PolicyVersionResponse(
            id=v.id,
            version=v.version,
            policy_yaml=v.policy_yaml,
            created_at=v.created_at.isoformat() if v.created_at else None,
        )
        for v in versions
    ]


@router.post("/{policy_id}/activate")
async def activate_version(
    policy_id: uuid.UUID,
    body: ActivateVersionRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = PolicyService(db)
    try:
        await service.activate_version(policy_id, body.version_id, auth.org_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"status": "activated", "version_id": str(body.version_id)}


@router.post("/{policy_id}/simulate")
async def simulate_policy(
    policy_id: uuid.UUID,
    body: SimulateRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = PolicyService(db)
    try:
        result = service.simulate(body.policy_yaml, body.namespace)
    except PolicyLoadError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return result
