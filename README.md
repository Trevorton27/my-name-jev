# JevOps

AI Decision Reliability Control Plane.

Evaluates proposed AI agent actions using TypeSafe AI's Jev model for fast typed semantic judgments, then applies deterministic Python policy rules to return one of four dispositions: **ALLOW**, **RETRY**, **HUMAN_REVIEW**, or **BLOCK**.

## Quick Start

```bash
# Start infrastructure
make up

# Install dependencies
make install

# Run migrations
make migrate

# Start API server
make dev
```

## Development

```bash
make lint      # Check code style
make format    # Auto-format code
make test      # Run tests
```

## Architecture

```
                         ┌──────────────────────┐
                         │       Vercel          │
                         │   Next.js Web Console │
                         │   (Operations UI)     │
                         └──────────┬────────────┘
                                    │
                          NEXT_PUBLIC_API_URL
                            (HTTPS requests)
                                    │
                                    ▼
┌───────────────────────────────────────────────────────┐
│                      Railway                          │
│                                                       │
│   ┌───────────────────┐      ┌──────────────────┐    │
│   │   API Service      │      │  Worker Service   │    │
│   │   (FastAPI)        │      │  (Celery)         │    │
│   │                    │      │                   │    │
│   │ - Decision engine  │      │ - Async tasks     │    │
│   │ - Policy eval      │ ───▶ │ - Drift detection │    │
│   │ - REST API         │ task │ - Replay runs     │    │
│   │ - Alembic migrate  │ queue│                   │    │
│   └────────┬───────────┘      └─────────┬─────────┘    │
│            │                            │              │
└────────────┼────────────────────────────┼──────────────┘
             │                            │
        ┌────┴────┐                 ┌─────┴─────┐
        │  Neon   │                 │  Upstash  │
        │Postgres │                 │   Redis   │
        │         │                 │           │
        │ - Orgs  │                 │ - Celery  │
        │ - Agents│                 │   broker  │
        │ - Deci- │                 │ - Result  │
        │   sions │                 │   backend │
        │ - Poli- │                 │ - Rate    │
        │   cies  │                 │   limits  │
        └─────────┘                 └───────────┘

                    ┌───────────────┐
                    │  AI Agent     │
                    │  (Your App)   │
                    └───────┬───────┘
                            │
                   POST /v1/decisions
                   X-API-Key header
                            │
                            ▼
                    ┌───────────────┐
                    │  JevOps API   │
                    │  (Railway)    │
                    └───────────────┘
                            │
                    Evaluate action via
                    Jev model + policies
                            │
                            ▼
                 ┌─────────────────────┐
                 │  ALLOW | RETRY |    │
                 │  HUMAN_REVIEW |     │
                 │  BLOCK              │
                 └─────────────────────┘
```

**Request flow:** An AI agent sends a proposed action to the JevOps API on Railway. The API evaluates it using the Jev model (TypeSafe AI) for semantic judgment, then applies deterministic policy rules, and returns a disposition. The Celery worker on Railway handles async tasks like drift detection and replay runs, using Upstash Redis as the message broker. The Next.js console on Vercel provides a UI for reviewing decisions, managing policies, and monitoring agents.

## Integrations

### Upstream: TypeSafe AI (Jev model)

JevOps gets its semantic judgments from TypeSafe AI's **Jev** model through the [`typesafe-sdk`](https://pypi.org/project/typesafe-sdk/) package (`apps/api/src/jevops/jev/typesafe_provider.py`).

| API | Used for |
|---|---|
| `AsyncTypeSafeClient.system_one(state, questions)` | One call per evaluation. Sends the action, objective, state and evidence, and asks typed questions: `Noul` (0–1 appropriateness), `Score` (risk 1–10) and `Choice` (recommended route). |

The provider is chosen by `JEVOPS_JEV_PROVIDER`:

| Value | Behaviour |
|---|---|
| `mock` (default) | Deterministic judgments seeded from the input; no external calls |
| `typesafe` | Real Jev model; requires `JEVOPS_JEV_API_KEY` |
| `failure` | Simulates provider timeouts / errors for testing |

If the model call fails, the decision falls back to `human_review` and the error is recorded in `policy_trace`; a failure never becomes `allow`.

> The SDK's own `TYPESAFE_API_KEY` variable is **not** read. JevOps always passes `JEVOPS_JEV_API_KEY` to the client explicitly.

### Downstream: Support Buddy X9000

[Support Buddy X9000](https://github.com/Trevorton27/The-Support-Buddy-X9000) uses JevOps as a gate on AI-drafted customer replies. It authenticates with a JevOps API key and the seeded `SupportBuddy` agent (`30000000-0000-0000-0000-000000000002`).

| Endpoint | Called by Support Buddy when | Purpose |
|---|---|---|
| `POST /v1/decisions/evaluate` | The guardrails agent runs (`action_type: send_customer_reply`) | Get a disposition for the drafted reply. A `block` fails Support Buddy's guardrails. |
| `GET /v1/decisions/{id}` | An investigation page is viewed | Show the decision, judgments and matched rule in the UI |
| `POST /v1/decisions/{id}/outcome` | A human approves (`allow`) or rejects (`block`) the reply | Ground truth for calibration |
| `POST /v1/decisions/evaluate` | A Devin fix task finishes with a PR (`action_type: merge_devin_fix`, custom questions) | Merge-readiness review of Devin's PR; `retry` can send feedback back to Devin |
| `POST /v1/decisions/{id}/outcome` | GitHub reports that Devin's PR was merged (`allow`) or closed (`block`) | Calibrate Jev's judgments of Devin's work |

Support Buddy sends `X-Correlation-ID: <investigation run id>` and an idempotency key `guardrails-<run id>`, so retried runs reuse the same decision. It treats JevOps as optional: on any error it continues with its local guardrails.

Any other agent can integrate the same way, over HTTP or with the Python SDK in `packages/python-sdk/` (see `examples/support_buddy/`).

### Web console

The Next.js console (`apps/web`, deployed on Vercel) calls the same REST API with `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_API_KEY`. That key is bundled into the browser, so anyone who can open the console can read it.

## API Reference

All `/v1` endpoints except `/v1/health` and `/v1/demo/reset` require an `X-API-Key: jvo_<env>_<prefix>_<secret>` header. Demo reset instead requires `X-Demo-Reset-Token`. Results are scoped to the key's organization.

| Method & path | Description |
|---|---|
| `GET /health` | Liveness check (used by the Railway healthcheck) |
| `POST /v1/decisions/evaluate` | Evaluate a proposed action → decision with disposition, judgments, policy trace |
| `GET /v1/decisions` | List decisions |
| `GET /v1/decisions/{id}` | Get one decision |
| `POST /v1/decisions/{id}/outcome` | Record the real-world outcome (ground truth label) |
| `POST /v1/decisions/{id}/feedback` | Attach free-text feedback |
| `GET /v1/reviews` · `GET /v1/reviews/{id}` | Human review queue |
| `POST /v1/reviews/{id}/approve` · `/reject` · `/request-retry` · `/correct-judgments` | Resolve a review |
| `POST /v1/policies` · `GET /v1/policies` · `GET /v1/policies/{id}` | Manage policies |
| `POST /v1/policies/{id}/versions` · `GET /v1/policies/{id}/versions` | Policy versions |
| `POST /v1/policies/{id}/activate` · `POST /v1/policies/{id}/simulate` | Activate / dry-run a policy |
| `POST /v1/replays` · `GET /v1/replays` · `GET /v1/replays/{id}` · `POST /v1/replays/{id}/execute` | Replay past decisions against a policy |
| `GET /v1/analytics/overview` · `/dispositions` · `/overrides` | Dashboard metrics |
| `POST /v1/demo/reset` | **Destructive:** wipes all data, reseeds demo data, returns a new API key. Disabled (403) unless `JEVOPS_SECURITY_DEMO_RESET_TOKEN` is set; requires a matching `X-Demo-Reset-Token` header |

## Configuration

Environment variables for the API service (see `.env.example`):

| Variable | Purpose |
|---|---|
| `JEVOPS_DB_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_NAME` | Postgres (Neon) |
| `JEVOPS_REDIS_HOST` / `_PORT` / `_PASSWORD` / `_SSL` / `_DB` | Redis (Upstash): Celery broker and rate limits |
| `JEVOPS_JEV_PROVIDER` | `mock` \| `typesafe` \| `failure` |
| `JEVOPS_JEV_API_KEY` | TypeSafe API key (required when provider is `typesafe`) |
| `JEVOPS_JEV_MODEL` / `_TIMEOUT` / `_MAX_RETRIES` | Jev model options |
| `JEVOPS_SECURITY_API_KEY_PEPPER` | Pepper for hashing API keys; changing it invalidates every key |
| `JEVOPS_SECURITY_CORS_ORIGINS` | Allowed origins (include the console's URL) |
| `JEVOPS_SECURITY_DEMO_RESET_TOKEN` | Enables `POST /v1/demo/reset` when set. Leave unset in production |

## Deployment

- **API (Railway):** the service's **Root Directory must be `/apps/api`**. The Dockerfile, `start.sh` and `railway.toml` live there. Built from the repo root, Railway falls back to Railpack and fails with `start.sh not found`. Set the healthcheck path to `/health`. On startup the container runs `alembic upgrade head` and then starts uvicorn.
- **Worker (Railway):** same image, start command from `apps/api/railway-worker.toml`.
- **Console (Vercel):** `apps/web`.

Full walkthrough: [`docs/deployment.md`](docs/deployment.md).

### Registering an agent

To add an agent to an existing org without the destructive demo reset (idempotent, supports `--dry-run`):

```bash
cd apps/api
# with JEVOPS_DB_* pointing at the target database
uv run python -m jevops.database.add_agent --key-prefix jvo_test_<prefix> --dry-run
uv run python -m jevops.database.add_agent --key-prefix jvo_test_<prefix>
```

## Project Structure

```
jevops/
├── apps/api/          # FastAPI backend
├── apps/web/          # Next.js operations console
├── packages/python-sdk/  # Python client SDK
├── docs/              # Documentation
├── policies/examples/ # Example policy definitions
└── docker-compose.yml # PostgreSQL + Redis
```
