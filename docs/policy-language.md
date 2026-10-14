# Policy Language

Policies are defined in YAML and consist of questions, rules, and a default disposition.

## Structure

```yaml
name: My Policy
description: What this policy controls
action_types: [create_pr, deploy]

questions:
  evidence_sufficient:
    type: noul
    instructions: Is there sufficient evidence?
  risk_level:
    type: score
    instructions: Rate risk 1-10
    criteria: [harm, reversibility]
  recommended_route:
    type: choice
    instructions: Recommended route?
    criteria:
      allow: Safe
      block: Unsafe

rules:
  - name: auto_allow
    when:
      all:
        - evidence_sufficient >= 0.8
        - risk_level <= 3.0
    then: allow
    priority: 10
    reason: Low risk

  - name: block_high_risk
    when: risk_level >= 9.0
    then: block
    priority: 20

default: human_review
```

## Question Types

- **noul**: Probability 0-1. Access as float in rules.
- **choice**: Categorical selection. Access as string.
- **score**: Numeric score. Access as float. Confidence available via `{key}_confidence`.

## Rule Conditions

- **Single expression**: `when: "risk_level >= 5.0"`
- **All (AND)**: `when.all: [expr1, expr2]`
- **Any (OR)**: `when.any: [expr1, expr2]`

## Expression Language

Safe subset of Python expressions:
- Comparisons: `>=`, `<=`, `>`, `<`, `==`, `!=`
- Boolean: `and`, `or`, `not`
- Membership: `in`, `not in`
- Constants: strings, numbers, booleans
- Variables: question keys from the namespace

Blocked: function calls, imports, lambdas, dunder access.

## Rule Evaluation

Rules are sorted by priority (lower = higher priority). First match wins. If no rule matches, the `default` disposition is used.
