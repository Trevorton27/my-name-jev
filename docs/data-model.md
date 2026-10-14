# Data Model

## Entity Relationship

```
Organization 1──* Project 1──* Agent
     |                |
     *                *
  APIKey           Policy 1──* PolicyVersion
                               |
                          Decision *──1 PolicyVersion
                            |  |
                            *  *
                       Judgment Review
                            |
                     DecisionOutcome
```

## Tables

### Organization
Multi-tenant root entity. All resources are scoped to an organization.

### Project
Groups agents and policies. Has a `mode`: OBSERVE (log-only) or ENFORCE (actionable).

### Agent
An AI agent that submits actions for evaluation.

### APIKey
Prefixed API keys (`jvo_live_*` / `jvo_test_*`) for authentication. Secret stored as SHA-256 hash with pepper.

### Policy / PolicyVersion
YAML-defined policy rules. Versions are immutable. `active_version_id` determines which version is used for evaluation.

### Decision
Core entity: records an evaluation request and its disposition (ALLOW, RETRY, HUMAN_REVIEW, BLOCK).

### Judgment
Individual Jev model outputs (Noul, Choice, Score) attached to a decision.

### Review
Created when a decision gets HUMAN_REVIEW disposition. Tracks reviewer actions.

### DecisionOutcome
Ground-truth label and outcome data for calibration.

### ReplayRun
Batch re-evaluation of historical decisions with different policies/thresholds.

### AuditEvent
Immutable audit log for all significant actions.
