"""Demo data seeder for JevOps."""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from jevops.auth.api_key import generate_api_key, hash_api_key
from jevops.config import get_settings
from jevops.models.agent import Agent
from jevops.models.api_key import APIKey
from jevops.models.audit_event import AuditEvent
from jevops.models.decision import Decision, Disposition, Judgment
from jevops.models.decision_outcome import DecisionOutcome
from jevops.models.organization import Organization
from jevops.models.policy import Policy, PolicyVersion
from jevops.models.project import Project, ProjectMode
from jevops.models.replay import ReplayRun, ReplayStatus
from jevops.models.review import Review, ReviewStatus

DEMO_ORG_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
DEMO_PROJECT_IDS = [
    uuid.UUID("20000000-0000-0000-0000-000000000001"),
    uuid.UUID("20000000-0000-0000-0000-000000000002"),
]
DEMO_AGENT_IDS = [uuid.UUID("30000000-0000-0000-0000-00000000000" + str(i)) for i in range(1, 5)]

DEMO_POLICY_YAML = """
name: Demo Engineering Policy
action_types: [create_pr, deploy, send_email, escalate_incident]
questions:
  action_appropriate:
    type: noul
    instructions: Is this action appropriate?
  risk_level:
    type: score
    instructions: Rate operational risk 1-10.
    criteria: [harm, reversibility, scope]
  recommended_route:
    type: choice
    instructions: Recommended disposition?
    criteria:
      allow: Safe to proceed
      retry: Needs modification
      human_review: Needs human judgment
      block: Should not proceed
rules:
  - name: auto_allow
    when:
      all:
        - action_appropriate >= 0.8
        - risk_level <= 3.0
    then: allow
    priority: 10
    reason: Low risk with strong evidence
  - name: block_critical
    when: risk_level >= 9.0
    then: block
    priority: 20
    reason: Critical risk
  - name: review_high_risk
    when: risk_level >= 6.0
    then: human_review
    priority: 30
    reason: High risk needs review
default: retry
"""


async def seed_demo_data(session: AsyncSession) -> dict[str, str]:
    """Seed demo data and return summary."""
    pepper = get_settings().security.api_key_pepper

    # Organization
    org = Organization(id=DEMO_ORG_ID, name="Demo Organization", slug="demo")
    session.add(org)
    await session.flush()

    # Projects
    projects = [
        Project(
            id=DEMO_PROJECT_IDS[0],
            org_id=DEMO_ORG_ID,
            name="Backend Services",
            slug="backend",
            mode=ProjectMode.ENFORCE.value,
            organization_id=DEMO_ORG_ID,
        ),
        Project(
            id=DEMO_PROJECT_IDS[1],
            org_id=DEMO_ORG_ID,
            name="Customer Support",
            slug="support",
            mode=ProjectMode.OBSERVE.value,
            organization_id=DEMO_ORG_ID,
        ),
    ]
    session.add_all(projects)
    await session.flush()

    # API Key
    full_key, prefix, secret = generate_api_key("test")
    api_key = APIKey(
        org_id=DEMO_ORG_ID,
        name="Demo Key",
        prefix=prefix,
        key_hash=hash_api_key(secret, pepper),
        environment="test",
        organization_id=DEMO_ORG_ID,
    )
    session.add(api_key)

    # Agents
    agent_names = ["CodeBot", "SupportBuddy", "InfraAgent", "DataPipeline"]
    agents = []
    for i, name in enumerate(agent_names):
        agent = Agent(
            id=DEMO_AGENT_IDS[i],
            org_id=DEMO_ORG_ID,
            name=name,
            slug=name.lower(),
            project_id=DEMO_PROJECT_IDS[i % 2],
        )
        agents.append(agent)
    session.add_all(agents)
    await session.flush()

    # Policy + versions
    policy_id = uuid.uuid4()
    version_id = uuid.uuid4()
    policy = Policy(
        id=policy_id,
        org_id=DEMO_ORG_ID,
        name="Demo Engineering Policy",
        slug="demo-eng",
        action_types=["create_pr", "deploy", "send_email"],
        project_id=DEMO_PROJECT_IDS[0],
        active_version_id=None,
    )
    session.add(policy)
    await session.flush()

    version = PolicyVersion(
        id=version_id,
        policy_id=policy_id,
        version=1,
        policy_yaml=DEMO_POLICY_YAML,
        parsed_config={},
    )
    session.add(version)
    await session.flush()

    policy.active_version_id = version_id

    # v2 of the policy
    v2_id = uuid.uuid4()
    v2 = PolicyVersion(
        id=v2_id,
        policy_id=policy_id,
        version=2,
        policy_yaml=DEMO_POLICY_YAML.replace("auto_allow", "auto_allow_v2"),
        parsed_config={},
    )
    session.add(v2)

    await session.flush()

    # Decisions (100+)
    action_types = ["create_pr", "deploy", "send_email", "escalate_incident"]
    dispositions = list(Disposition)
    decisions = []
    for i in range(120):
        d = random.choice(dispositions).value
        now = datetime.utcnow() - timedelta(hours=random.randint(0, 720))
        decision = Decision(
            org_id=DEMO_ORG_ID,
            agent_id=random.choice(DEMO_AGENT_IDS),
            action_type=random.choice(action_types),
            action={"description": f"Demo action {i}"},
            objective=f"Demo objective {i}",
            state={"step": i},
            evidence={"score": random.random()},
            disposition=d,
            policy_trace={"engine": "demo"},
            provider_latency_ms=random.uniform(10, 500),
            provider_model="mock",
            environment="test",
            mode="observe" if i % 3 == 0 else "enforce",
            created_at=now,
        )
        decisions.append(decision)
        session.add(decision)

    await session.flush()

    # Judgments for each decision
    for decision in decisions:
        session.add(
            Judgment(
                decision_id=decision.id,
                question_key="action_appropriate",
                question_type="noul",
                value={"value": round(random.random(), 3)},
                confidence=None,
            )
        )
        session.add(
            Judgment(
                decision_id=decision.id,
                question_key="risk_level",
                question_type="score",
                value={"value": round(random.uniform(1, 10), 1)},
                confidence=round(random.uniform(0.5, 1.0), 3),
            )
        )

    # Reviews (20+)
    review_decisions = [d for d in decisions if d.disposition == Disposition.HUMAN_REVIEW.value][:25]
    for dec in review_decisions:
        status = random.choice(list(ReviewStatus)).value
        review = Review(
            org_id=DEMO_ORG_ID,
            decision_id=dec.id,
            status=status,
            reviewer="demo-reviewer" if status != ReviewStatus.PENDING.value else None,
            reason="Demo review" if status != ReviewStatus.PENDING.value else None,
        )
        session.add(review)
        if status == ReviewStatus.APPROVED.value:
            dec.final_disposition = Disposition.ALLOW.value
        elif status == ReviewStatus.REJECTED.value:
            dec.final_disposition = Disposition.BLOCK.value

    # Outcomes (15+)
    for dec in decisions[:18]:
        outcome = DecisionOutcome(
            org_id=DEMO_ORG_ID,
            decision_id=dec.id,
            ground_truth_label=random.choice(["allow", "block", "human_review"]),
            outcome_data={"success": random.choice([True, False])},
        )
        session.add(outcome)

    # Replay runs
    replay_completed = ReplayRun(
        org_id=DEMO_ORG_ID,
        name="Policy v2 Test",
        status=ReplayStatus.COMPLETED.value,
        total_decisions=50,
        completed_decisions=48,
        failed_decisions=2,
        agreement_rate=0.82,
        results_summary={"agreements": 40, "changes": {"allow->block": 3, "retry->allow": 5}},
    )
    replay_running = ReplayRun(
        org_id=DEMO_ORG_ID,
        name="Threshold Experiment",
        status=ReplayStatus.RUNNING.value,
        total_decisions=100,
        completed_decisions=45,
        failed_decisions=1,
    )
    session.add_all([replay_completed, replay_running])

    # Audit events
    for _ in range(30):
        event = AuditEvent(
            org_id=DEMO_ORG_ID,
            event_type=random.choice(
                [
                    "decision.evaluated",
                    "review.approved",
                    "review.rejected",
                    "policy.activated",
                    "api_key.created",
                ]
            ),
            actor="demo-system",
            resource_type=random.choice(["decision", "review", "policy"]),
            resource_id=str(uuid.uuid4()),
        )
        session.add(event)

    await session.commit()

    return {
        "api_key": full_key,
        "org_id": str(DEMO_ORG_ID),
        "decisions": str(len(decisions)),
        "reviews": str(len(review_decisions)),
    }


async def run_seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.db.async_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        result = await seed_demo_data(session)
        print("Demo data seeded successfully!")
        print(f"  API Key: {result['api_key']}")
        print(f"  Org ID: {result['org_id']}")
        print(f"  Decisions: {result['decisions']}")
        print(f"  Reviews: {result['reviews']}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_seed())
