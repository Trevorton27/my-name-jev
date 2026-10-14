from jevops.models import DecisionResponse, EvaluateRequest, JudgmentResponse


def test_evaluate_request_defaults():
    req = EvaluateRequest(agent_id="test-agent", action_type="deploy")
    assert req.environment == "test"
    assert req.action == {}
    assert req.state == {}
    assert req.idempotency_key is None


def test_decision_response_properties():
    d = DecisionResponse(
        id="123", disposition="allow", action_type="test",
        mode="enforce", environment="live",
    )
    assert d.is_allowed is True
    assert d.needs_review is False
    assert d.is_blocked is False

    d2 = DecisionResponse(
        id="456", disposition="human_review", action_type="test",
        mode="enforce", environment="live",
    )
    assert d2.is_allowed is False
    assert d2.needs_review is True

    d3 = DecisionResponse(
        id="789", disposition="block", action_type="test",
        mode="enforce", environment="live",
    )
    assert d3.is_blocked is True


def test_decision_response_with_judgments():
    d = DecisionResponse(
        id="123", disposition="allow", action_type="test",
        mode="enforce", environment="live",
        judgments=[
            JudgmentResponse(
                question_key="risk", question_type="score",
                value=3.5, confidence=0.9,
            ),
        ],
    )
    assert len(d.judgments) == 1
    assert d.judgments[0].confidence == 0.9
