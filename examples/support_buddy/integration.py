"""Shows JevOps evaluation integrated into a Support Buddy workflow."""
import sys
sys.path.insert(0, "../../packages/python-sdk/src")

from jevops import JevOpsClient, EvaluateRequest
from scenarios import SCENARIOS


AGENT_ID = "00000000-0000-0000-0000-000000000002"


def run_scenario(client: JevOpsClient, name: str, scenario: dict) -> None:
    print(f"\n{'='*60}")
    print(f"Scenario: {name}")
    print(f"Action: {scenario['action_type']}")
    print(f"Objective: {scenario['objective']}")

    decision = client.evaluate(EvaluateRequest(
        agent_id=AGENT_ID,
        action_type=scenario["action_type"],
        action=scenario["action"],
        objective=scenario["objective"],
        state=scenario["state"],
        evidence=scenario["evidence"],
    ))

    print(f"\nDisposition: {decision.disposition.upper()}")
    print(f"Provider: {decision.provider_model}")
    if decision.provider_latency_ms:
        print(f"Latency: {decision.provider_latency_ms:.1f}ms")

    for j in decision.judgments:
        print(f"  {j.question_key}: {j.value}", end="")
        if j.confidence:
            print(f" (confidence: {j.confidence:.2f})", end="")
        print()

    if decision.is_allowed:
        print("-> Proceeding with action")
    elif decision.needs_review:
        print("-> Queued for human review")
    elif decision.is_blocked:
        print("-> Action blocked by policy")
    else:
        print("-> Retrying with modifications")


def main():
    client = JevOpsClient(
        base_url="http://localhost:8000",
        api_key="jvo_test_demo1234_abcdef1234567890abcdef1234567890",
    )

    for name, scenario in SCENARIOS.items():
        run_scenario(client, name, scenario)

    client.close()
    print(f"\n{'='*60}")
    print("All scenarios complete.")


if __name__ == "__main__":
    main()
