# Support Buddy X9000 Integration

## Overview

JevOps integrates with Support Buddy X9000 to evaluate AI agent actions before execution. This is a self-contained example — it does not modify the Support Buddy codebase.

## Flow

```
Support Buddy proposes action
  → JevOps SDK sends evaluation request
  → Jev evaluates semantic questions
  → Policy engine applies rules
  → Disposition returned to Support Buddy
  → If HUMAN_REVIEW: support team reviews
  → Outcome recorded for calibration
```

## Example Scenarios

1. **Start Investigation Session**: Low-risk read-only action → likely ALLOW
2. **Create PR**: Code change with tests → depends on risk/evidence
3. **Send Customer Response**: Communication with external party → tone/accuracy check
4. **Escalate Incident**: Severity override → requires justification
5. **Retry Investigation**: Broader scope retry → needs additional evidence

## SDK Usage

```python
from jevops import JevOpsClient, EvaluateRequest

client = JevOpsClient(base_url="...", api_key="jvo_live_...")

decision = client.evaluate(EvaluateRequest(
    agent_id="support-buddy-agent-id",
    action_type="send_email",
    action={"to": "customer@example.com", "body": "..."},
    objective="Respond to support ticket",
    state={"ticket_id": "1234"},
    evidence={"resolution_verified": True},
))

if decision.is_allowed:
    execute_action()
elif decision.needs_review:
    queue_for_review()
```

See `examples/support_buddy/` for full runnable examples.
