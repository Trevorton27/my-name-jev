"""Basic agent integration example using the JevOps SDK."""
import sys
sys.path.insert(0, "../../packages/python-sdk/src")

from jevops import JevOpsClient, EvaluateRequest


def main():
    client = JevOpsClient(
        base_url="http://localhost:8000",
        api_key="jvo_test_demo1234_abcdef1234567890abcdef1234567890",
    )

    # Propose an action
    decision = client.evaluate(EvaluateRequest(
        agent_id="00000000-0000-0000-0000-000000000001",
        action_type="send_email",
        action={
            "to": "customer@example.com",
            "subject": "Your support request #1234",
            "body": "We've resolved your issue. The database connection timeout was increased.",
        },
        objective="Respond to customer support ticket about database timeouts",
        state={"ticket_id": "1234", "priority": "medium"},
        evidence={"resolution_verified": True, "similar_tickets_resolved": 5},
    ))

    print(f"Decision ID: {decision.id}")
    print(f"Disposition: {decision.disposition}")
    print(f"Mode: {decision.mode}")

    if decision.is_allowed:
        print("Action is ALLOWED - proceed with sending the email")
    elif decision.needs_review:
        print("Action needs HUMAN REVIEW - waiting for approval")
    elif decision.is_blocked:
        print("Action is BLOCKED - do not proceed")
    else:
        print(f"Action should be RETRIED - disposition: {decision.disposition}")

    # Record outcome
    if decision.is_allowed:
        client.record_outcome(decision.id, {
            "ground_truth_label": "allow",
            "outcome_data": {"customer_responded": True, "satisfaction": "positive"},
        })

    client.close()


if __name__ == "__main__":
    main()
