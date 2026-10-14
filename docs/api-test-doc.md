# JevOps API Testing Guide

## Prerequisites

```bash
# 1. Start infrastructure
make up          # Postgres (port 5433) + Redis

# 2. Run migrations
make migrate     # Alembic upgrade head

# 3. Seed demo data
make seed        # Creates org, projects, agents, decisions, reviews, etc.
```

The seed outputs a demo API key. Save it — you'll need it for every authenticated request:

```
API Key: jvo_test_<prefix>_<secret>
Org ID:  10000000-0000-0000-0000-000000000001
```

If you lose the key, reset the demo:

```bash
# requires JEVOPS_SECURITY_DEMO_RESET_TOKEN to be set on the API
curl -s -X POST http://localhost:8000/v1/demo/reset -H "X-Demo-Reset-Token: $JEVOPS_SECURITY_DEMO_RESET_TOKEN" | python3 -m json.tool
```

## Starting the API Server

```bash
make dev
# or directly:
uv run uvicorn jevops.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Authentication

All `/v1/` endpoints (except `/v1/health` and `/v1/demo/reset`, which uses `X-Demo-Reset-Token`) require the `X-API-Key` header:

```bash
-H "X-API-Key: jvo_test_<prefix>_<secret>"
```

Unauthenticated requests return `401 Missing API key`.

---

## Endpoints

### Health

```bash
# Root health check
curl http://localhost:8000/health
# {"status":"ok"}

# v1 health check
curl http://localhost:8000/v1/health
# {"status":"ok","version":"0.1.0"}
```

---

### Decisions

#### Evaluate a Decision

Submits an action for evaluation. The provider (mock by default) generates semantic judgments, and the policy engine (or simple disposition logic) determines the disposition.

```bash
curl -s -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "30000000-0000-0000-0000-000000000001",
    "action_type": "deploy",
    "action": {
      "service": "billing-api",
      "version": "2.1.0",
      "environment": "production"
    },
    "objective": "Deploy billing API v2.1.0 to production",
    "state": {
      "tests_passing": true,
      "approval_count": 2
    },
    "evidence": {
      "changelog": "Fix rate limiting bug",
      "test_coverage": 0.92
    },
    "environment": "test"
  }' | python3 -m json.tool
```

**Response:**
```json
{
    "id": "a1b2c3d4-...",
    "disposition": "allow",
    "final_disposition": null,
    "action_type": "deploy",
    "mode": "observe",
    "environment": "test",
    "judgments": [
        {
            "question_key": "action_appropriate",
            "question_type": "noul",
            "value": 0.87,
            "probabilities": null,
            "confidence": null
        },
        {
            "question_key": "risk_level",
            "question_type": "score",
            "value": 3.2,
            "probabilities": null,
            "confidence": 0.75
        },
        {
            "question_key": "recommended_route",
            "question_type": "choice",
            "value": "allow",
            "probabilities": {"allow": 0.7, "retry": 0.15, "human_review": 0.1, "block": 0.05},
            "confidence": 0.7
        }
    ],
    "policy_trace": {"engine": "simple", "namespace": {...}},
    "provider_latency_ms": 0.5,
    "provider_model": "mock",
    "correlation_id": null,
    "created_at": "2026-09-29T..."
}
```

**Dispositions:** `allow`, `retry`, `human_review`, `block`

#### Evaluate with Custom Questions

```bash
curl -s -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "30000000-0000-0000-0000-000000000001",
    "action_type": "send_email",
    "action": {"to": "customer@example.com", "subject": "Account update"},
    "objective": "Send account status update to customer",
    "questions": {
      "tone_appropriate": {
        "type": "noul",
        "instructions": "Is the tone appropriate for a customer-facing email?"
      },
      "data_sensitivity": {
        "type": "score",
        "instructions": "Rate data sensitivity from 1 (public) to 10 (highly confidential).",
        "criteria": ["PII exposure", "financial data", "internal details"]
      },
      "recommended_action": {
        "type": "choice",
        "instructions": "What should we do with this email?",
        "criteria": {
          "allow": "Safe to send",
          "retry": "Needs editing",
          "human_review": "Needs manager approval",
          "block": "Do not send"
        }
      }
    }
  }' | python3 -m json.tool
```

#### Evaluate with Idempotency

```bash
curl -s -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "30000000-0000-0000-0000-000000000001",
    "action_type": "create_pr",
    "action": {"repo": "backend", "branch": "fix/auth-bug"},
    "idempotency_key": "pr-fix-auth-bug-20260929"
  }' | python3 -m json.tool
```

Re-submitting the same `idempotency_key` returns the original decision without re-evaluation.

#### Evaluate with Correlation ID

```bash
curl -s -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "X-Correlation-ID: inv-run-abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "30000000-0000-0000-0000-000000000001",
    "action_type": "escalate_incident",
    "action": {"incident_id": "INC-42", "escalate_to": "on-call"}
  }' | python3 -m json.tool
```

The response includes the correlation ID, useful for tracing decisions back to investigation runs.

#### List Decisions

```bash
# List recent decisions (default: 50, max offset pagination)
curl -s "http://localhost:8000/v1/decisions?limit=10&offset=0" \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool

# Response: array of DecisionResponse objects
```

#### Get a Single Decision

```bash
curl -s http://localhost:8000/v1/decisions/DECISION_UUID \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Record an Outcome (Ground Truth)

After observing the real-world result of a decision, record it for calibration:

```bash
curl -s -X POST http://localhost:8000/v1/decisions/DECISION_UUID/outcome \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "ground_truth_label": "allow",
    "outcome_data": {
      "success": true,
      "incident_created": false,
      "customer_impact": "none"
    }
  }' | python3 -m json.tool
```

#### Record Feedback

```bash
curl -s -X POST http://localhost:8000/v1/decisions/DECISION_UUID/feedback \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "This should have been blocked — the deploy caused a P1 incident."
  }' | python3 -m json.tool
```

---

### Reviews

Decisions with `disposition: "human_review"` create review records automatically.

#### List Reviews

```bash
# All reviews
curl -s "http://localhost:8000/v1/reviews" \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool

# Filter by status
curl -s "http://localhost:8000/v1/reviews?status=pending" \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

**Statuses:** `pending`, `approved`, `rejected`, `retry_requested`

#### Get a Single Review

```bash
curl -s http://localhost:8000/v1/reviews/REVIEW_UUID \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Approve a Review

```bash
curl -s -X POST http://localhost:8000/v1/reviews/REVIEW_UUID/approve \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer": "alice@example.com",
    "reason": "Low risk deploy to staging, tests passing",
    "notes": "Approved after checking CI results"
  }' | python3 -m json.tool
```

Sets `final_disposition: "allow"` on the linked decision.

#### Reject a Review

```bash
curl -s -X POST http://localhost:8000/v1/reviews/REVIEW_UUID/reject \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer": "bob@example.com",
    "reason": "This deploy targets production during a freeze window"
  }' | python3 -m json.tool
```

Sets `final_disposition: "block"` on the linked decision.

#### Request Retry

```bash
curl -s -X POST http://localhost:8000/v1/reviews/REVIEW_UUID/request-retry \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer": "carol@example.com",
    "reason": "Needs additional test coverage before proceeding"
  }' | python3 -m json.tool
```

Sets `final_disposition: "retry"` on the linked decision.

#### Correct Judgments

Override the model's original judgment values (creates calibration data):

```bash
curl -s -X POST http://localhost:8000/v1/reviews/REVIEW_UUID/correct-judgments \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer": "dave@example.com",
    "corrected_judgments": {
      "risk_level": 8.5,
      "action_appropriate": 0.3
    },
    "notes": "Model underestimated risk — this touches payment processing"
  }' | python3 -m json.tool
```

---

### Policies

#### Create a Policy

```bash
curl -s -X POST http://localhost:8000/v1/policies \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deploy Safety Policy",
    "slug": "deploy-safety",
    "project_id": "20000000-0000-0000-0000-000000000001",
    "action_types": ["deploy", "rollback"],
    "policy_yaml": "name: Deploy Safety Policy\naction_types: [deploy, rollback]\nquestions:\n  action_appropriate:\n    type: noul\n    instructions: Is this deploy safe?\n  risk_level:\n    type: score\n    instructions: Rate risk 1-10.\n    criteria: [blast radius, reversibility]\nrules:\n  - name: auto_allow\n    when:\n      all:\n        - action_appropriate >= 0.8\n        - risk_level <= 3.0\n    then: allow\n    priority: 10\n    reason: Low risk with high confidence\n  - name: block_critical\n    when: risk_level >= 9.0\n    then: block\n    priority: 20\n    reason: Critical risk\ndefault: human_review\n"
  }' | python3 -m json.tool
```

#### List Policies

```bash
curl -s http://localhost:8000/v1/policies \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Get a Policy

```bash
curl -s http://localhost:8000/v1/policies/POLICY_UUID \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Create a New Policy Version

```bash
curl -s -X POST http://localhost:8000/v1/policies/POLICY_UUID/versions \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_yaml": "name: Deploy Safety Policy v2\naction_types: [deploy]\nquestions:\n  risk_level:\n    type: score\n    instructions: Rate risk 1-10.\n    criteria: [blast radius]\nrules:\n  - name: auto_allow\n    when: risk_level <= 2.0\n    then: allow\n    priority: 10\n    reason: Very low risk\ndefault: human_review\n"
  }' | python3 -m json.tool
```

#### List Policy Versions

```bash
curl -s http://localhost:8000/v1/policies/POLICY_UUID/versions \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Activate a Version

```bash
curl -s -X POST http://localhost:8000/v1/policies/POLICY_UUID/activate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": "VERSION_UUID"
  }' | python3 -m json.tool
```

#### Simulate a Policy

Test a policy against a hypothetical namespace without persisting anything:

```bash
curl -s -X POST http://localhost:8000/v1/policies/POLICY_UUID/simulate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_yaml": "name: Test\naction_types: [deploy]\nquestions:\n  risk_level:\n    type: score\n    instructions: Rate risk.\n    criteria: [scope]\nrules:\n  - name: auto_allow\n    when: risk_level <= 3.0\n    then: allow\n    priority: 10\n    reason: Low risk\n  - name: block_high\n    when: risk_level >= 8.0\n    then: block\n    priority: 20\n    reason: High risk\ndefault: human_review\n",
    "namespace": {
      "risk_level": 2.5
    }
  }' | python3 -m json.tool
```

**Response includes a full trace** showing which rules were evaluated, matched, and skipped.

---

### Analytics

#### Overview

```bash
curl -s http://localhost:8000/v1/analytics/overview \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Disposition Breakdown

```bash
curl -s "http://localhost:8000/v1/analytics/dispositions?days=30" \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Override Statistics

```bash
curl -s http://localhost:8000/v1/analytics/overrides \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

---

### Replays

#### Create a Replay Run

```bash
curl -s -X POST http://localhost:8000/v1/replays \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Policy v2 Comparison",
    "description": "Test new thresholds against historical decisions"
  }' | python3 -m json.tool
```

#### List Replays

```bash
curl -s http://localhost:8000/v1/replays \
  -H "X-API-KEY: YOUR_API_KEY" | python3 -m json.tool
```

#### Get Replay Details

```bash
curl -s http://localhost:8000/v1/replays/REPLAY_UUID \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

#### Execute a Replay

```bash
curl -s -X POST http://localhost:8000/v1/replays/REPLAY_UUID/execute \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

---

### Demo Management

#### Reset Demo Data

Clears all data and re-seeds. Returns a fresh API key.

```bash
# requires JEVOPS_SECURITY_DEMO_RESET_TOKEN to be set on the API
curl -s -X POST http://localhost:8000/v1/demo/reset -H "X-Demo-Reset-Token: $JEVOPS_SECURITY_DEMO_RESET_TOKEN" | python3 -m json.tool
```

**Response:**
```json
{
    "status": "reset",
    "api_key": "jvo_test_<new_prefix>_<new_secret>",
    "details": {
        "api_key": "jvo_test_...",
        "org_id": "10000000-0000-0000-0000-000000000001",
        "decisions": "120",
        "reviews": "25"
    }
}
```

**Note:** This endpoint does not require authentication.

---

## Demo Agent IDs

The seed creates four demo agents you can use in evaluation requests:

| Agent | ID | Project |
|---|---|---|
| CodeBot | `30000000-0000-0000-0000-000000000001` | Backend Services |
| SupportBuddy | `30000000-0000-0000-0000-000000000002` | Customer Support |
| InfraAgent | `30000000-0000-0000-0000-000000000003` | Backend Services |
| DataPipeline | `30000000-0000-0000-0000-000000000004` | Customer Support |

## Demo Project IDs

| Project | ID | Mode |
|---|---|---|
| Backend Services | `20000000-0000-0000-0000-000000000001` | enforce |
| Customer Support | `20000000-0000-0000-0000-000000000002` | observe |

---

## End-to-End Test Scenarios

### 1. Allow Flow

```bash
# High-confidence, low-risk action → ALLOW
curl -s -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "30000000-0000-0000-0000-000000000001",
    "action_type": "create_pr",
    "action": {"title": "Fix typo in README"},
    "state": {"tests_passing": true},
    "evidence": {"risk": "minimal", "scope": "documentation only"}
  }' | python3 -m json.tool
```

### 2. Human Review Flow

```bash
# Evaluate → get HUMAN_REVIEW → find review → approve
DECISION=$(curl -s -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "30000000-0000-0000-0000-000000000001",
    "action_type": "deploy",
    "action": {"service": "payments", "env": "production"},
    "state": {"change_risk": "high"},
    "evidence": {"affected_customers": 50000}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Decision ID: $DECISION"

# Check pending reviews
curl -s "http://localhost:8000/v1/reviews?status=pending" \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool
```

### 3. Provider Failure → Safe Fallback

Set `JEVOPS_JEV_PROVIDER=failure` in your environment, then evaluate. The system will never silently return ALLOW — it falls back to `human_review`.

### 4. Org Isolation

Requests scoped to one API key's organization cannot see another organization's decisions, reviews, or policies.

---

## Error Responses

| Status | Meaning |
|---|---|
| `401` | Missing or invalid `X-API-Key` |
| `404` | Resource not found (or belongs to a different org) |
| `422` | Validation error (bad policy YAML, invalid request body) |
| `429` | Rate limit exceeded (default: 60 requests/minute) |
| `500` | Internal server error |

All errors return JSON:
```json
{"detail": "Error description"}
```

---

## Rate Limiting

Default: 60 requests per minute per client IP. Configurable via `JEVOPS_SECURITY_RATE_LIMIT_PER_MINUTE`.

When exceeded:
```json
{"detail": "Rate limit exceeded"}
```

## Request Size Limit

Default: 1MB. Configurable via `JEVOPS_SECURITY_MAX_REQUEST_SIZE_BYTES`.

## CORS

Default allowed origin: `http://localhost:3000`. Configurable via `JEVOPS_SECURITY_CORS_ORIGINS`.
