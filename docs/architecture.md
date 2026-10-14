# JevOps Architecture

## Overview

JevOps is an AI Decision Reliability Control Plane that evaluates proposed AI agent actions using TypeSafe AI's Jev model for fast typed semantic judgments, then applies deterministic Python policy rules to return one of four dispositions: **ALLOW**, **RETRY**, **HUMAN_REVIEW**, or **BLOCK**.

## Core Flow

```
Agent proposes action
  → JevOps receives evaluation request
  → Jev model produces semantic judgments (Noul/Choice/Score)
  → Policy engine evaluates rules against judgments
  → Disposition returned to agent
  → If HUMAN_REVIEW: reviewer approves/rejects
  → Outcome recorded for calibration
```

## Key Assumptions

1. **Jev is the semantic layer.** JevOps does not duplicate Jev's judgment capabilities — it wraps them with policy, governance, and calibration.
2. **Policies are deterministic.** Given the same Jev outputs, the same policy always produces the same disposition. No randomness in policy evaluation.
3. **Multi-tenant by default.** Every resource is scoped to an organization. Cross-tenant access is never permitted.
4. **Provider abstraction.** The system supports swappable Jev providers (real TypeSafe, mock, failure simulation) behind a common protocol.
5. **Async-first.** All I/O operations use async patterns. Sync fallbacks exist only for tooling (e.g., Alembic migrations).

## Technology Stack

- **API:** FastAPI + Pydantic v2
- **Database:** PostgreSQL 16 via SQLAlchemy 2.0 (async) + Alembic
- **Cache/Broker:** Redis 7
- **Background Jobs:** Celery
- **Observability:** structlog + OpenTelemetry
- **Frontend:** Next.js 14+ / TypeScript / Tailwind / shadcn/ui
- **Jev Integration:** typesafe-sdk (PyPI)

## Package Structure

- `apps/api` — FastAPI backend (main application)
- `apps/web` — Next.js operations console
- `packages/python-sdk` — Client SDK for integrating with JevOps

---

## File Tree

```
jevops/
├── apps/
│   ├── api/                          # FastAPI backend (Railway)
│   │   ├── Dockerfile
│   │   ├── railway.toml              # Railway API service config
│   │   ├── railway-worker.toml       # Railway Celery worker config
│   │   ├── start.sh                  # Entrypoint: migrate + uvicorn
│   │   └── src/jevops/
│   │       ├── main.py               # App factory, middleware stack, lifespan
│   │       ├── config.py             # Pydantic Settings (JEVOPS_* env vars)
│   │       │
│   │       ├── api/                  # HTTP layer
│   │       │   ├── middleware.py      # Rate-limit, request-size, secure headers
│   │       │   ├── errors.py         # Exception handlers
│   │       │   └── v1/
│   │       │       ├── router.py     # Mounts all v1 sub-routers
│   │       │       ├── decisions.py  # POST /v1/decisions — core endpoint
│   │       │       ├── policies.py   # CRUD for policy definitions
│   │       │       ├── reviews.py    # Human review queue
│   │       │       ├── replays.py    # Policy replay runs
│   │       │       ├── analytics.py  # Metrics & drift endpoints
│   │       │       ├── health.py     # /v1/health
│   │       │       └── demo.py       # /v1/demo/reset (seed helper)
│   │       │
│   │       ├── auth/                 # Authentication
│   │       │   ├── api_key.py        # Key generation, hashing (SHA-256+pepper)
│   │       │   └── middleware.py      # X-API-Key header → AuthContext
│   │       │
│   │       ├── decisions/            # Decision domain
│   │       │   ├── schemas.py        # EvaluateRequest/Response Pydantic models
│   │       │   └── service.py        # DecisionService: provider → policy → persist
│   │       │
│   │       ├── policies/             # Policy engine
│   │       │   ├── engine.py         # Evaluates rules against Jev judgments
│   │       │   ├── expression.py     # AST-based safe expression evaluator
│   │       │   ├── loader.py         # YAML policy loader
│   │       │   ├── schema.py         # Policy Pydantic models
│   │       │   └── service.py        # PolicyService CRUD
│   │       │
│   │       ├── jev/                   # Jev model integration (swappable)
│   │       │   ├── protocol.py        # DecisionModelProvider protocol
│   │       │   ├── types.py           # TypedQuestion, JudgmentResult, etc.
│   │       │   ├── mock_provider.py   # Deterministic mock for dev/test
│   │       │   ├── typesafe_provider.py # Real TypeSafe SDK integration
│   │       │   └── failure_provider.py  # Simulates failures for testing
│   │       │
│   │       ├── reviews/              # Human review domain
│   │       │   ├── schemas.py
│   │       │   └── service.py
│   │       │
│   │       ├── replays/              # Policy replay domain
│   │       │   ├── engine.py         # Re-evaluates historical decisions
│   │       │   ├── schemas.py
│   │       │   └── service.py
│   │       │
│   │       ├── analytics/            # Metrics & drift detection
│   │       │   ├── drift.py          # Drift detection algorithms
│   │       │   ├── metrics.py        # Disposition/latency aggregations
│   │       │   ├── queries.py        # Analytics SQL queries
│   │       │   └── service.py
│   │       │
│   │       ├── models/               # SQLAlchemy ORM models
│   │       │   ├── organization.py   # Org (tenant root)
│   │       │   ├── project.py        # Project (org child)
│   │       │   ├── agent.py          # Agent identity
│   │       │   ├── api_key.py        # Hashed API key
│   │       │   ├── decision.py       # Decision + Judgment
│   │       │   ├── policy.py         # Policy + PolicyVersion
│   │       │   ├── review.py         # Human review record
│   │       │   ├── replay.py         # Replay run + results
│   │       │   ├── decision_outcome.py
│   │       │   └── audit_event.py
│   │       │
│   │       ├── database/             # DB infrastructure
│   │       │   ├── engine.py         # Async engine + session factory
│   │       │   ├── session.py        # get_session dependency
│   │       │   ├── base.py           # Declarative base
│   │       │   ├── seed.py           # Demo data seeder
│   │       │   └── repositories/     # Data access layer
│   │       │       ├── base.py
│   │       │       ├── api_key_repo.py
│   │       │       ├── decision_repo.py
│   │       │       └── policy_repo.py
│   │       │
│   │       ├── workers/              # Celery async tasks
│   │       │   ├── celery_app.py     # Celery app (Upstash Redis broker)
│   │       │   └── tasks/
│   │       │       ├── audit_write.py    # Async audit log writes
│   │       │       ├── replay.py         # Background replay runs
│   │       │       └── review_notify.py  # Review notification dispatch
│   │       │
│   │       ├── integrations/         # Webhooks & external integrations
│   │       │   ├── schemas.py
│   │       │   └── webhooks.py
│   │       │
│   │       ├── observability/        # Logging, metrics, tracing
│   │       │   ├── logging.py        # structlog setup
│   │       │   ├── metrics.py        # Prometheus/OTel metrics
│   │       │   └── tracing.py        # OpenTelemetry tracing
│   │       │
│   │       └── alembic/              # Database migrations
│   │           ├── env.py
│   │           └── versions/
│   │               └── 001_initial.py
│   │
│   └── web/                          # Next.js console (Vercel)
│       ├── vercel.json
│       └── app/
│           ├── layout.tsx            # Root layout + sidebar
│           ├── sidebar.tsx
│           ├── providers.tsx         # TanStack Query provider
│           ├── globals.css
│           ├── page.tsx              # Dashboard home
│           ├── decisions/
│           │   ├── page.tsx          # Decision list
│           │   └── [id]/page.tsx     # Decision detail
│           ├── policies/
│           │   ├── page.tsx          # Policy list
│           │   └── [id]/page.tsx     # Policy editor
│           ├── reviews/page.tsx      # Human review queue
│           ├── replays/
│           │   ├── page.tsx          # Replay run list
│           │   └── [id]/page.tsx     # Replay detail
│           ├── analytics → calibration/page.tsx
│           ├── audit/page.tsx        # Audit log
│           └── integrations/page.tsx # Webhook config
│
├── packages/
│   └── python-sdk/                   # Client SDK (PyPI)
│       ├── src/jevops/
│       │   ├── client.py            # Sync client
│       │   ├── async_client.py      # Async client
│       │   ├── models.py            # Request/response models
│       │   ├── exceptions.py        # SDK exceptions
│       │   └── retry.py             # Retry/backoff logic
│       └── tests/
│
├── policies/examples/                # Example YAML policy definitions
├── docs/                             # Documentation
└── docker-compose.yml                # Local dev: Postgres + Redis
```

---

## Logic Flow

The following diagrams trace a decision request from ingress to response,
then show how background work and the web console connect.

### 1. Decision Request (critical path)

```
AI Agent
  │
  │  POST /v1/decisions
  │  X-API-Key: jvo_live_xxx
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ main.py  →  FastAPI middleware stack                         │
│   CORSMiddleware → RequestSizeLimit → RateLimit → SecureHdr │
│   → Correlation-ID injection                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ auth/middleware.py                                           │
│   Extract X-API-Key header                                  │
│   → api_key.py: SHA-256 + pepper hash → lookup in DB        │
│   → Produce AuthContext { org_id, key_id, scopes }          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ api/v1/decisions.py  (route handler)                         │
│   Validate EvaluateRequest (Pydantic)                       │
│   → Instantiate DecisionService                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ decisions/service.py  →  DecisionService.evaluate()          │
│                                                              │
│   1. Idempotency check (decision_repo)                      │
│   2. Build TypedQuestions (Noul / Choice / Score)            │
│   3. Call Jev provider ─────────────────────┐               │
│                                              │               │
│      ┌───────────────────────────────────────┘               │
│      │                                                       │
│      ▼                                                       │
│   jev/protocol.py  (DecisionModelProvider)                   │
│      ├── mock_provider.py      (dev/test)                   │
│      ├── typesafe_provider.py  (production — TypeSafe SDK)  │
│      └── failure_provider.py   (chaos testing)              │
│                                                              │
│   4. Convert JudgmentResults → namespace dict               │
│   5. Evaluate disposition ──────────────────┐               │
│                                              │               │
│      ┌───────────────────────────────────────┘               │
│      │                                                       │
│      ▼                                                       │
│   policies/engine.py  (PolicyEngine)                         │
│      → loader.py:  load YAML policy rules                   │
│      → expression.py:  AST-safe eval of rule conditions     │
│      → Returns disposition + policy trace                   │
│                                                              │
│   6. Persist Decision + Judgments (decision_repo → Postgres) │
│   7. Enqueue async tasks (Celery → Upstash Redis)           │
│      → audit_write    (audit log)                           │
│      → review_notify  (if HUMAN_REVIEW)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Response to Agent  │
              │  { disposition:     │
              │    ALLOW | RETRY |  │
              │    HUMAN_REVIEW |   │
              │    BLOCK }          │
              └─────────────────────┘
```

### 2. Background Workers (Celery on Railway)

```
┌──────────────────────────────────────────────────┐
│  Upstash Redis (broker)                          │
│    queue/1: task messages                        │
│    queue/2: result backend                       │
└───────────┬──────────────────────────────────────┘
            │  consume
            ▼
┌──────────────────────────────────────────────────┐
│  workers/celery_app.py                           │
│                                                  │
│  tasks/audit_write.py                            │
│    → Write audit_event rows to Postgres          │
│                                                  │
│  tasks/review_notify.py                          │
│    → Send webhook / notification for reviews     │
│    → integrations/webhooks.py                    │
│                                                  │
│  tasks/replay.py                                 │
│    → replays/engine.py: re-evaluate historical   │
│      decisions against a new policy version      │
│    → Write ReplayRun + results to Postgres       │
└──────────────────────────────────────────────────┘
```

### 3. Web Console (Next.js on Vercel)

```
┌──────────────────────────────────────────────────┐
│  Vercel — apps/web                               │
│                                                  │
│  app/page.tsx ─────────────── Dashboard overview │
│  app/decisions/ ───────────── Browse decisions   │
│  app/policies/ ────────────── Manage policies    │
│  app/reviews/ ─────────────── Human review queue │
│  app/replays/ ─────────────── Replay run results │
│  app/calibration/ ─────────── Drift & metrics    │
│  app/audit/ ───────────────── Audit event log    │
│  app/integrations/ ────────── Webhook config     │
│                                                  │
│  All pages fetch via NEXT_PUBLIC_API_URL          │
│  using TanStack Query (providers.tsx)            │
└───────────────────┬──────────────────────────────┘
                    │
                    │  HTTPS (NEXT_PUBLIC_API_URL)
                    ▼
            ┌───────────────┐
            │  Railway API  │
            └───────────────┘
```

### 4. End-to-End Data Flow Summary

```
AI Agent ──POST──▶ Railway API ──query──▶ Jev Provider (TypeSafe/mock)
                       │                        │
                       │◀──judgments────────────-┘
                       │
                       ├──eval──▶ Policy Engine ──▶ disposition
                       │
                       ├──write─▶ Neon Postgres (decisions, judgments)
                       │
                       ├──enqueue─▶ Upstash Redis ──▶ Celery Worker
                       │                                  │
                       │                         write audit/notify/replay
                       │                                  │
                       │◀─────────────────────────────────┘
                       │
Vercel Console ──GET──▶ Railway API ──read──▶ Neon Postgres
```
