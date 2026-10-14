"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("slug", name=op.f("uq_organizations_slug")),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False, server_default="observe"),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], name=op.f("fk_projects_organization_id_organizations")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_org_id"), "projects", ["org_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("prefix", sa.String(30), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("environment", sa.String(10), nullable=False, server_default="test"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], name=op.f("fk_api_keys_organization_id_organizations")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_keys")),
        sa.UniqueConstraint("prefix", name=op.f("uq_api_keys_prefix")),
    )
    op.create_index(op.f("ix_api_keys_prefix"), "api_keys", ["prefix"])
    op.create_index("ix_api_keys_org_id", "api_keys", ["org_id"])

    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_agents_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agents")),
    )
    op.create_index("ix_agents_org_id", "agents", ["org_id"])

    op.create_table(
        "policy_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("policy_yaml", sa.Text(), nullable=False),
        sa.Column("parsed_config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy_versions")),
    )

    op.create_table(
        "policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("action_types", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("active_version_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["active_version_id"], ["policy_versions.id"], name=op.f("fk_policies_active_version_id_policy_versions")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_policies_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policies")),
    )
    op.create_index("ix_policies_org_id", "policies", ["org_id"])

    # Add FK from policy_versions to policies (circular)
    op.create_foreign_key(
        op.f("fk_policy_versions_policy_id_policies"),
        "policy_versions",
        "policies",
        ["policy_id"],
        ["id"],
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("policy_version_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", sa.String(255), nullable=False),
        sa.Column("action", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("state", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("disposition", sa.String(20), nullable=False),
        sa.Column("final_disposition", sa.String(20), nullable=True),
        sa.Column("policy_trace", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("provider_latency_ms", sa.Float(), nullable=True),
        sa.Column("provider_model", sa.String(63), nullable=True),
        sa.Column("environment", sa.String(20), nullable=False, server_default="test"),
        sa.Column("mode", sa.String(10), nullable=False, server_default="observe"),
        sa.Column("correlation_id", sa.String(255), nullable=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], name=op.f("fk_decisions_agent_id_agents")),
        sa.ForeignKeyConstraint(
            ["policy_version_id"], ["policy_versions.id"], name=op.f("fk_decisions_policy_version_id_policy_versions")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decisions")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_decisions_idempotency_key")),
    )
    op.create_index("ix_decisions_idempotency_key", "decisions", ["idempotency_key"])
    op.create_index("ix_decisions_correlation_id", "decisions", ["correlation_id"])
    op.create_index("ix_decisions_org_id", "decisions", ["org_id"])

    op.create_table(
        "judgments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("question_key", sa.String(255), nullable=False),
        sa.Column("question_type", sa.String(20), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], name=op.f("fk_judgments_decision_id_decisions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_judgments")),
    )
    op.create_index("ix_judgments_decision_id", "judgments", ["decision_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewer", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("corrected_judgments", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], name=op.f("fk_reviews_decision_id_decisions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
    )
    op.create_index("ix_reviews_decision_id", "reviews", ["decision_id"])
    op.create_index("ix_reviews_org_id", "reviews", ["org_id"])

    op.create_table(
        "decision_outcomes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("ground_truth_label", sa.String(20), nullable=True),
        sa.Column("outcome_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["decision_id"], ["decisions.id"], name=op.f("fk_decision_outcomes_decision_id_decisions")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_decision_outcomes")),
        sa.UniqueConstraint("decision_id", name=op.f("uq_decision_outcomes_decision_id")),
    )
    op.create_index("ix_decision_outcomes_decision_id", "decision_outcomes", ["decision_id"])
    op.create_index("ix_decision_outcomes_org_id", "decision_outcomes", ["org_id"])

    op.create_table(
        "replay_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("policy_version_id", sa.Uuid(), nullable=True),
        sa.Column("provider_config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("total_decisions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_decisions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_decisions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("agreement_rate", sa.Float(), nullable=True),
        sa.Column("results_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_version_id"], ["policy_versions.id"], name=op.f("fk_replay_runs_policy_version_id_policy_versions")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_replay_runs")),
    )
    op.create_index("ix_replay_runs_org_id", "replay_runs", ["org_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(255), nullable=True),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_org_id", "audit_events", ["org_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("replay_runs")
    op.drop_table("decision_outcomes")
    op.drop_table("reviews")
    op.drop_table("judgments")
    op.drop_table("decisions")
    op.drop_constraint(op.f("fk_policy_versions_policy_id_policies"), "policy_versions", type_="foreignkey")
    op.drop_table("policies")
    op.drop_table("policy_versions")
    op.drop_table("agents")
    op.drop_table("api_keys")
    op.drop_table("projects")
    op.drop_table("organizations")
