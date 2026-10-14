"""Register an agent in an existing organization without touching other data.

Unlike the demo seeder, this never deletes anything. It is idempotent: if the
agent already exists it reports it and exits.

Usage (with JEVOPS_DB_* pointing at the target database):
    uv run python -m jevops.database.add_agent --key-prefix jvo_test_ab12cd34 --dry-run
    uv run python -m jevops.database.add_agent --key-prefix jvo_test_ab12cd34

The org is resolved from --key-prefix (the API key the client authenticates
with, so decisions and the agent land in the same org), else --org-id, else
the only organization in the database.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from jevops.config import get_settings
from jevops.models.agent import Agent
from jevops.models.api_key import APIKey
from jevops.models.organization import Organization
from jevops.models.project import Project, ProjectMode

SUPPORT_BUDDY_AGENT_ID = uuid.UUID("30000000-0000-0000-0000-000000000002")


def _key_prefix(value: str) -> str:
    """Accept either a prefix (jvo_test_ab12cd34) or a full key; keep only the prefix."""
    prefix = "_".join(value.strip().split("_")[:3])
    if not re.fullmatch(r"jvo_(test|live)_[0-9a-f]{8}", prefix):
        raise argparse.ArgumentTypeError(f"expected jvo_<test|live>_<8 hex chars>, got {prefix!r}")
    return prefix


async def _resolve_org(session: AsyncSession, args: argparse.Namespace) -> uuid.UUID:
    if args.key_prefix:
        api_key = (await session.execute(select(APIKey).where(APIKey.prefix == args.key_prefix))).scalar_one_or_none()
        if not api_key:
            sys.exit(f"No API key with prefix {args.key_prefix}")
        if not api_key.is_active:
            print(f"Warning: API key {args.key_prefix} is inactive")
        return api_key.organization_id

    if args.org_id:
        return args.org_id

    orgs = (await session.execute(select(Organization))).scalars().all()
    if len(orgs) != 1:
        sys.exit(f"Found {len(orgs)} organizations; pass --key-prefix or --org-id")
    return orgs[0].id


async def _resolve_project(session: AsyncSession, org_id: uuid.UUID, args: argparse.Namespace) -> tuple[Project, bool]:
    """Return (project, created). Prefers --project-id, then slug 'support', then any project."""
    if args.project_id:
        project = await session.get(Project, args.project_id)
        if not project or project.organization_id != org_id:
            sys.exit(f"Project {args.project_id} not found in org {org_id}")
        return project, False

    projects = (await session.execute(select(Project).where(Project.organization_id == org_id))).scalars().all()
    for project in projects:
        if project.slug == "support":
            return project, False
    if projects:
        return projects[0], False

    project = Project(
        org_id=org_id,
        organization_id=org_id,
        name="Customer Support",
        slug="support",
        mode=ProjectMode.OBSERVE.value,
    )
    session.add(project)
    await session.flush()
    return project, True


async def add_agent(args: argparse.Namespace) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.db.async_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print(f"Database: {settings.db.host}/{settings.db.name}")
            org_id = await _resolve_org(session, args)
            print(f"Organization: {org_id}")

            existing = await session.get(Agent, args.agent_id)
            if existing:
                print(f"Agent {existing.id} already exists ({existing.name}, org {existing.org_id})")
                if existing.org_id != org_id:
                    print("Warning: it belongs to a different org than the API key")
                return

            project, project_created = await _resolve_project(session, org_id, args)
            print(f"Project: {project.name} ({project.id}){' [new]' if project_created else ''}")

            agent = Agent(
                id=args.agent_id,
                org_id=org_id,
                name=args.name,
                slug=args.slug,
                description="Support Buddy X9000 customer reply agent",
                project_id=project.id,
            )
            session.add(agent)
            await session.flush()

            if args.dry_run:
                await session.rollback()
                print(f"Dry run: would create agent {agent.id} ({agent.name})")
                return

            await session.commit()
            print(f"Created agent {agent.id} ({agent.name})")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--key-prefix", type=_key_prefix, help="API key prefix (or full key) whose org to use")
    parser.add_argument("--org-id", type=uuid.UUID, help="Organization ID (if no --key-prefix)")
    parser.add_argument("--project-id", type=uuid.UUID, help="Project to attach the agent to")
    parser.add_argument("--agent-id", type=uuid.UUID, default=SUPPORT_BUDDY_AGENT_ID)
    parser.add_argument("--name", default="SupportBuddy")
    parser.add_argument("--slug", default="supportbuddy")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen, then roll back")
    asyncio.run(add_agent(parser.parse_args()))


if __name__ == "__main__":
    main()
