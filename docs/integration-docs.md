# Integrating JevOps with The Support Buddy X9000

## Overview

[The Support Buddy X9000](https://github.com/Trevorton27/The-Support-Buddy-X9000) is an agentic AI platform that autonomously investigates support tickets using a 9-agent LangGraph pipeline, then routes results through human-in-the-loop approval before dispatching Devin AI for bug reproduction and code fixes.

JevOps adds a **decision reliability layer** to this pipeline. Instead of relying solely on the built-in guardrails agent (regex + GPT-4o-mini) and manual HITL routing, JevOps evaluates every autonomous action — sending customer replies, escalating incidents, creating PRs, deploying fixes — through typed semantic judgments and deterministic policy rules, returning one of four dispositions: **ALLOW**, **RETRY**, **HUMAN_REVIEW**, or **BLOCK**.

### What Changes

| Before (SB X9000 standalone) | After (with JevOps) |
|---|---|
| Guardrails agent runs PII/secret regex + LLM pass/fail | JevOps evaluates the full action context with typed questions (noul, score, choice) and policy rules |
| HITL approval is always required after investigation | JevOps can auto-ALLOW low-risk actions, auto-BLOCK critical ones, and route only ambiguous cases to human review |
| No confidence calibration or drift detection | JevOps tracks ground-truth outcomes, computes Brier scores and ECE, and detects distribution drift |
| No replay or what-if analysis | JevOps replays historical decisions against new policies to measure impact before deploying changes |

### What Doesn't Change

- The 9-agent investigation pipeline runs as before
- Inngest orchestration is unchanged
- Devin AI integration is unaffected
- The existing guardrails agent still runs (JevOps augments it, doesn't replace it)

---

## Architecture

```
Support Buddy X9000                              JevOps
─────────────────                              ──────

Ticket arrives
  │
  ▼
[9-Agent Pipeline]
  │
  ├─ Guardrails Agent (existing) ─────────────► POST /v1/decisions/evaluate
  │    PII/secret regex still runs                 ├─ Jev typed judgments
  │    LLM guardrails still runs                   ├─ Policy rule evaluation
  │                                                └─ Returns: disposition + trace
  │                                                         │
  │  ◄──────────────────────────────────────────────────────┘
  │
  ├─ if disposition == "allow" → proceed to escalation agent
  ├─ if disposition == "retry" → re-draft reply, re-run guardrails
  ├─ if disposition == "human_review" → route to HITL approval queue
  └─ if disposition == "block" → halt pipeline, flag for review

[HITL Approval] (if needed)
  │
  ├─ Approve  ──► POST /v1/decisions/{id}/outcome { ground_truth_label: "allow" }
  └─ Reject   ──► POST /v1/decisions/{id}/outcome { ground_truth_label: "block" }

[Devin Dispatch]
  │
  ├─ "reproduce" action ──► POST /v1/decisions/evaluate { action_type: "devin_reproduce" }
  └─ "fix" action ─────────► POST /v1/decisions/evaluate { action_type: "devin_fix" }
```

---

## Setup

### 1. JevOps Side

Ensure JevOps is running locally or on a reachable host:

```bash
cd jevops/
make up          # Postgres + Redis
make migrate     # Apply schema
make seed        # Creates demo org, agents, policies
make dev         # Start API on :8000
```

Save the API key from the seed output:
```
API Key: jvo_test_d67e77ec_bceb06cd3cd544abc569bc028ff1650a
```

### 2. Support Buddy Side

Add the following to your `.env.local`:

```env
# JevOps Integration
JEVOPS_API_URL=http://localhost:8000
JEVOPS_API_KEY=jvo_test_<prefix>_<secret>
JEVOPS_AGENT_ID=30000000-0000-0000-0000-000000000002
JEVOPS_ENABLED=true
```

The `JEVOPS_AGENT_ID` should correspond to a registered agent in JevOps. The demo seed includes `SupportBuddy` (`30000000-0000-0000-0000-000000000002`) in the "Customer Support" project.

### 3. Register the Agent in JevOps (Production)

For production use, register your Support Buddy instance as an agent via the API:

```bash
# First, create an org and project if not using the demo seed
# Then create an API key for the SB X9000 integration
```

---

## Integration Points

### Integration Point 1: Guardrails Agent Enhancement

The primary integration point is the **guardrails agent** (`agents/nodes/guardrails-agent.ts`). Currently it runs deterministic regex checks and an LLM pass. With JevOps, it also calls the decision evaluation API.

Create a new file `lib/integrations/jevops/client.ts`:

```typescript
import { getEnv } from "@/lib/env";
import { createLogger } from "@/lib/logger";

const logger = createLogger("jevops-client");

export interface JevOpsDecision {
  id: string;
  disposition: "allow" | "retry" | "human_review" | "block";
  final_disposition: string | null;
  action_type: string;
  judgments: Array<{
    question_key: string;
    question_type: string;
    value: number | string;
    probabilities: Record<string, number> | null;
    confidence: number | null;
  }>;
  policy_trace: Record<string, unknown>;
  provider_latency_ms: number | null;
  correlation_id: string | null;
}

export interface EvaluateParams {
  agentId: string;
  actionType: string;
  action: Record<string, unknown>;
  objective?: string;
  state?: Record<string, unknown>;
  evidence?: Record<string, unknown>;
  correlationId?: string;
  idempotencyKey?: string;
}

export async function evaluateAction(params: EvaluateParams): Promise<JevOpsDecision | null> {
  const apiUrl = process.env.JEVOPS_API_URL;
  const apiKey = process.env.JEVOPS_API_KEY;

  if (!apiUrl || !apiKey || process.env.JEVOPS_ENABLED !== "true") {
    logger.info("JevOps not configured, skipping evaluation");
    return null;
  }

  try {
    const response = await fetch(`${apiUrl}/v1/decisions/evaluate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
        ...(params.correlationId ? { "X-Correlation-ID": params.correlationId } : {}),
      },
      body: JSON.stringify({
        agent_id: params.agentId,
        action_type: params.actionType,
        action: params.action,
        objective: params.objective,
        state: params.state || {},
        evidence: params.evidence || {},
        idempotency_key: params.idempotencyKey,
        environment: process.env.NODE_ENV === "production" ? "live" : "test",
      }),
      signal: AbortSignal.timeout(10_000), // 10s timeout
    });

    if (!response.ok) {
      logger.error("JevOps evaluation failed", {
        status: response.status,
        body: await response.text(),
      });
      return null; // Fail open — existing guardrails still apply
    }

    return (await response.json()) as JevOpsDecision;
  } catch (error) {
    logger.error("JevOps evaluation error", {
      error: error instanceof Error ? error.message : String(error),
    });
    return null; // Fail open
  }
}

export async function recordOutcome(
  decisionId: string,
  groundTruthLabel: string,
  outcomeData: Record<string, unknown> = {}
): Promise<void> {
  const apiUrl = process.env.JEVOPS_API_URL;
  const apiKey = process.env.JEVOPS_API_KEY;

  if (!apiUrl || !apiKey) return;

  try {
    await fetch(`${apiUrl}/v1/decisions/${decisionId}/outcome`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify({
        ground_truth_label: groundTruthLabel,
        outcome_data: outcomeData,
      }),
      signal: AbortSignal.timeout(5_000),
    });
  } catch (error) {
    logger.error("JevOps outcome recording failed", {
      error: error instanceof Error ? error.message : String(error),
    });
  }
}
```

### Integration Point 2: Modify the Guardrails Agent

Update `agents/nodes/guardrails-agent.ts` to call JevOps after the existing checks:

```typescript
// Add this import at the top
import { evaluateAction, type JevOpsDecision } from "@/lib/integrations/jevops/client";

// Inside guardrailsAgent(), after the existing deterministic + LLM checks:

    // --- Existing code produces: flags[], passed, guardrailsResult ---

    // Step 3: JevOps decision evaluation
    let jevopsDecision: JevOpsDecision | null = null;
    try {
      jevopsDecision = await evaluateAction({
        agentId: process.env.JEVOPS_AGENT_ID || "30000000-0000-0000-0000-000000000002",
        actionType: "send_customer_reply",
        action: {
          draft_reply: draft,
          ticket_id: state.ticket.id,
          ticket_title: state.ticket.title,
          ticket_severity: state.ticket.severity,
        },
        objective: "Send a customer-facing reply for a support ticket investigation",
        state: {
          investigation_run_id: state.runId,
          hypotheses_count: state.hypotheses.length,
          top_hypothesis_confidence: state.hypotheses[0]?.confidence ?? 0,
          guardrails_passed: passed,
          guardrails_flag_count: flags.length,
          blocking_flag_count: blockingFlags.length,
        },
        evidence: {
          has_incidents: state.incidents.length > 0,
          has_deployments: state.deployments.length > 0,
          knowledge_chunks_used: state.knowledgeChunks?.length ?? 0,
          customer_plan: state.customer?.plan ?? "unknown",
          customer_region: state.customer?.region ?? "unknown",
        },
        correlationId: state.runId,
        idempotencyKey: `guardrails-${state.runId}`,
      });
    } catch (err) {
      logger.warn("JevOps evaluation failed, proceeding with local guardrails only", {
        error: err instanceof Error ? err.message : String(err),
      });
    }

    // Merge JevOps disposition with local guardrails
    let finalPassed = passed;
    if (jevopsDecision) {
      if (jevopsDecision.disposition === "block") {
        finalPassed = false;
        flags.push({
          type: "policy" as GuardrailFlag["type"],
          severity: "block",
          description: `JevOps blocked: ${jevopsDecision.policy_trace?.matched_rule ?? "policy rule"}`,
          location: "jevops",
        });
      } else if (jevopsDecision.disposition === "human_review") {
        // Don't override local pass, but ensure HITL routing
        // The investigation will route to awaiting_approval anyway
      }
      // "allow" and "retry" don't override local guardrails
    }

    const guardrailsResult: GuardrailsResult = {
      passed: finalPassed,
      flags,
      revisedDraft: semanticResult.revisedDraft,
      // Store JevOps decision ID for traceability
      ...(jevopsDecision ? { jevopsDecisionId: jevopsDecision.id } : {}),
    };
```

> **Note:** You'll need to add `jevopsDecisionId?: string` and `"policy"` to the `GuardrailFlag["type"]` union in `agents/state.ts`.

### Integration Point 3: HITL Approval Outcome Recording

When a reviewer approves or rejects an investigation, record the outcome in JevOps for calibration. Update `app/api/investigations/[runId]/approve/route.ts`:

```typescript
import { recordOutcome } from "@/lib/integrations/jevops/client";

// After the existing approval logic:
if (jevopsDecisionId) {
  // Record the ground truth from the human review
  await recordOutcome(
    jevopsDecisionId,
    action === "approved" ? "allow" : "block",
    {
      reviewer_action: action,
      had_edits: originalDraft !== editedReply,
      reviewer_note: reviewerNote ?? undefined,
    }
  );
}
```

The `jevopsDecisionId` can be read from the investigation run's `guardrailsResult` JSON field.

### Integration Point 4: Devin AI Action Evaluation

Before dispatching Devin for reproduction or fix tasks, evaluate the action through JevOps:

```typescript
// In lib/integrations/devin/ or wherever Devin tasks are created:

import { evaluateAction } from "@/lib/integrations/jevops/client";

async function createDevinTaskWithEvaluation(
  mode: "reproduce" | "fix" | "defect_author",
  ticketId: string,
  investigationRunId: string,
  context: Record<string, unknown>
) {
  // Evaluate the Devin dispatch action
  const decision = await evaluateAction({
    agentId: process.env.JEVOPS_AGENT_ID || "30000000-0000-0000-0000-000000000002",
    actionType: `devin_${mode}`,
    action: {
      mode,
      ticket_id: ticketId,
      repository: process.env.DEVIN_DEFAULT_REPO,
    },
    objective: `Dispatch Devin to ${mode} a bug for ticket ${ticketId}`,
    state: {
      investigation_run_id: investigationRunId,
      mode,
    },
    evidence: context,
    correlationId: investigationRunId,
    idempotencyKey: `devin-${mode}-${ticketId}`,
  });

  // Respect JevOps disposition
  if (decision?.disposition === "block") {
    throw new Error(`JevOps blocked Devin ${mode}: ${JSON.stringify(decision.policy_trace)}`);
  }

  if (decision?.disposition === "human_review") {
    // Create the task but flag it for manual approval before execution
    // This integrates with SB X9000's existing HITL flow
  }

  // "allow" or "retry" (or null if JevOps unavailable) → proceed
  // ... existing Devin task creation logic ...
}
```

### Integration Point 5: Escalation Agent

The escalation agent decides whether to create GitHub issues or Jira tickets. Evaluate this through JevOps:

```typescript
// In agents/nodes/escalation-agent.ts, before creating external issues:

const decision = await evaluateAction({
  agentId: process.env.JEVOPS_AGENT_ID!,
  actionType: "escalate_incident",
  action: {
    escalation_type: escalationResult.action, // "github_issue", "jira_ticket", "page_oncall"
    severity: state.ticket.severity,
    target: escalationResult.target,
  },
  objective: `Escalate ticket ${state.ticket.id} via ${escalationResult.action}`,
  state: {
    investigation_run_id: state.runId,
    top_hypothesis: state.hypotheses[0]?.title,
    hypothesis_confidence: state.hypotheses[0]?.confidence,
  },
  evidence: {
    incident_count: state.incidents.length,
    deployment_count: state.deployments.length,
    customer_plan: state.customer?.plan,
  },
  correlationId: state.runId,
});

if (decision?.disposition === "block") {
  logger.warn("JevOps blocked escalation", { decision_id: decision.id });
  // Skip external escalation, add internal note instead
  return { escalationResult: { ...escalationResult, blocked_by_jevops: true } };
}
```

---

## JevOps Policy Configuration for SB X9000

Create a policy tailored to the Support Buddy's action types:

```bash
curl -s -X POST http://localhost:8000/v1/policies \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Buddy Policy",
    "slug": "support-buddy",
    "project_id": "20000000-0000-0000-0000-000000000002",
    "action_types": ["send_customer_reply", "escalate_incident", "devin_reproduce", "devin_fix"],
    "policy_yaml": "name: Support Buddy Policy\naction_types:\n  - send_customer_reply\n  - escalate_incident\n  - devin_reproduce\n  - devin_fix\nquestions:\n  action_appropriate:\n    type: noul\n    instructions: Is this action appropriate given the investigation evidence and customer context?\n  risk_level:\n    type: score\n    instructions: |\n      Rate the operational risk from 1 (trivial) to 10 (critical).\n      Consider: customer plan tier, blast radius, reversibility, PII exposure.\n    criteria:\n      - customer impact\n      - data sensitivity\n      - reversibility\n      - blast radius\n  recommended_route:\n    type: choice\n    instructions: What is the recommended disposition for this action?\n    criteria:\n      allow: Safe to proceed autonomously\n      retry: Needs modification (e.g., revised draft, different escalation path)\n      human_review: Requires human judgment before proceeding\n      block: Should not proceed under any circumstances\nrules:\n  - name: auto_allow_low_risk\n    when:\n      all:\n        - action_appropriate >= 0.85\n        - risk_level <= 3.0\n    then: allow\n    priority: 10\n    reason: High confidence and low risk — safe to proceed\n  - name: block_critical_risk\n    when: risk_level >= 9.0\n    then: block\n    priority: 20\n    reason: Critical risk — halt and flag\n  - name: review_high_risk\n    when: risk_level >= 6.0\n    then: human_review\n    priority: 30\n    reason: Elevated risk requires human oversight\n  - name: review_low_confidence\n    when: action_appropriate < 0.5\n    then: human_review\n    priority: 40\n    reason: Low confidence in action appropriateness\ndefault: retry\n"
  }' | python3 -m json.tool
```

### Action Types Mapped to SB X9000 Operations

| JevOps `action_type` | SB X9000 Operation | When Evaluated |
|---|---|---|
| `send_customer_reply` | Guardrails agent approves draft reply | After investigation, before HITL queue |
| `escalate_incident` | Escalation agent creates GitHub/Jira issue | During escalation agent node |
| `devin_reproduce` | Devin dispatched for bug reproduction | User clicks "Reproduce with Devin" |
| `devin_fix` | Devin dispatched for code fix + PR | User clicks "Send to Devin (Fix)" |

---

## Env Variable Reference

Add to SB X9000's `.env.local`:

```env
# JevOps Integration
JEVOPS_API_URL=http://localhost:8000    # JevOps API base URL
JEVOPS_API_KEY=jvo_test_<prefix>_<secret>  # JevOps API key
JEVOPS_AGENT_ID=<uuid>                  # Agent ID registered in JevOps
JEVOPS_ENABLED=true                     # Set to "false" to disable without removing code
```

Add to SB X9000's `lib/env.ts` Zod schema:

```typescript
// Optional — JevOps integration
JEVOPS_API_URL: z.string().url().optional(),
JEVOPS_API_KEY: z.string().optional(),
JEVOPS_AGENT_ID: z.string().uuid().optional(),
JEVOPS_ENABLED: z.enum(["true", "false"]).optional().default("false"),
```

---

## Fail-Open Design

The integration is designed to **fail open** — if JevOps is unreachable, misconfigured, or returns an error, the Support Buddy continues using its existing guardrails and HITL flow. JevOps adds a layer of evaluation; it never becomes a single point of failure.

Specifically:
- `evaluateAction()` returns `null` on any error → calling code skips JevOps logic
- `JEVOPS_ENABLED=false` disables all calls without code changes
- 10-second timeout prevents JevOps latency from blocking the pipeline
- JevOps itself never silently returns ALLOW on provider failure — it falls back to HUMAN_REVIEW

---

## Observability

### Correlation IDs

Every JevOps evaluation request includes `X-Correlation-ID: <investigationRunId>`. This links JevOps decisions back to SB X9000 investigation runs, enabling:

- Tracing a decision from the JevOps dashboard back to the SB X9000 investigation
- Querying all JevOps decisions for a specific investigation run
- Correlating JevOps latency with end-to-end pipeline timing

### Idempotency

Each evaluation uses `idempotency_key: "guardrails-{runId}"` (or `devin-{mode}-{ticketId}`). If the same action is evaluated twice (e.g., due to Inngest retry), JevOps returns the cached result without re-evaluation.

### Ground Truth Loop

```
SB X9000 Investigation
  │
  ├─ JevOps evaluates (disposition: X)
  │
  ├─ Human reviewer approves/rejects
  │
  └─ SB X9000 records outcome ──► JevOps /v1/decisions/{id}/outcome
                                    │
                                    └─ Feeds calibration metrics:
                                       Brier score, ECE, false-allow rate,
                                       false-block rate, override rate
```

Over time, this loop enables:
- **Calibration**: Are JevOps confidence scores well-calibrated?
- **Threshold tuning**: What confidence threshold minimizes false-allows without over-blocking?
- **Drift detection**: Are disposition distributions shifting over time?
- **Replay analysis**: Would a policy change have improved historical decisions?

---

## Testing the Integration

### 1. Verify Connectivity

```bash
# From the SB X9000 project directory
curl -s http://localhost:8000/health
# Should return: {"status":"ok"}
```

### 2. Test a Manual Evaluation

```bash
curl -s -X POST http://localhost:8000/v1/decisions/evaluate \
  -H "X-API-Key: YOUR_JEVOPS_KEY" \
  -H "X-Correlation-ID: test-investigation-001" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "30000000-0000-0000-0000-000000000002",
    "action_type": "send_customer_reply",
    "action": {
      "draft_reply": "Hi, we identified the issue as a database replica lag in us-east-1. Our team has promoted the standby replica and service should be restored.",
      "ticket_id": "test-ticket-001",
      "ticket_severity": "high"
    },
    "objective": "Send customer reply for database lag investigation",
    "state": {
      "hypotheses_count": 3,
      "top_hypothesis_confidence": 85,
      "guardrails_passed": true
    },
    "evidence": {
      "has_incidents": true,
      "customer_plan": "enterprise",
      "knowledge_chunks_used": 4
    }
  }' | python3 -m json.tool
```

### 3. Run the Full Pipeline

1. Start both apps:
   - JevOps: `make dev` (port 8000)
   - SB X9000: `npm run dev` (port 3000)
   - Inngest: `npx inngest-cli@latest dev`

2. Create a ticket in SB X9000 and run an investigation

3. Watch the guardrails agent call JevOps (visible in JevOps server logs)

4. Approve or reject in the SB X9000 approval queue

5. Check the JevOps decision was recorded:
   ```bash
   curl -s "http://localhost:8000/v1/decisions?limit=5" \
     -H "X-API-Key: YOUR_JEVOPS_KEY" | python3 -m json.tool
   ```

---

## Summary of Files to Create/Modify in SB X9000

| File | Action | Purpose |
|---|---|---|
| `lib/integrations/jevops/client.ts` | **Create** | JevOps API client (`evaluateAction`, `recordOutcome`) |
| `agents/nodes/guardrails-agent.ts` | **Modify** | Add JevOps evaluation after existing guardrails |
| `agents/state.ts` | **Modify** | Add `jevopsDecisionId` to `GuardrailsResult`, add `"policy"` to `GuardrailFlag["type"]` |
| `app/api/investigations/[runId]/approve/route.ts` | **Modify** | Record outcome in JevOps on approval/rejection |
| `lib/env.ts` | **Modify** | Add `JEVOPS_*` env vars to Zod schema |
| `.env.local` | **Modify** | Add `JEVOPS_API_URL`, `JEVOPS_API_KEY`, `JEVOPS_AGENT_ID`, `JEVOPS_ENABLED` |
