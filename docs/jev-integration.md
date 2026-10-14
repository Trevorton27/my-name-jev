# Jev Integration

JevOps integrates with TypeSafe AI's Jev model via the `typesafe-sdk` Python package.

## Provider Architecture

JevOps uses a provider abstraction (`DecisionModelProvider` protocol) that can be swapped:

- **MockProvider**: Deterministic outputs seeded from input hash. Profiles: balanced, cautious, permissive.
- **TypeSafeProvider**: Real Jev model via `AsyncTypeSafeClient`.
- **FailureProvider**: Simulates timeouts, rate limits, malformed responses.

## TypeSafe SDK Usage

```python
from typesafe_sdk import AsyncTypeSafeClient, Noul, Choice, Score

client = AsyncTypeSafeClient(api_key="...")
response = await client.system_one(
    state={"action": ..., "evidence": ...},
    questions={
        "appropriate": Noul(instructions="Is this appropriate?"),
        "route": Choice(instructions="Route?", criteria={"allow": "...", "block": "..."}),
        "risk": Score(instructions="Risk?", criteria=["harm", "scope"]),
    },
)
```

## Failure Policy

- Provider failures never silently convert to ALLOW
- High-risk failures fall back to HUMAN_REVIEW or BLOCK
- Failure reason is persisted in the decision record

## Configuration

Set `JEVOPS_JEV_PROVIDER=typesafe` and `TYPESAFE_API_KEY=...` to use the real Jev model.
