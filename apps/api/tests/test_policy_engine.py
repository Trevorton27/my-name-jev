import pytest

from jevops.policies.engine import PolicyEngine
from jevops.policies.loader import PolicyLoadError, load_policy_yaml

BASIC_POLICY = """
name: Test Policy
action_types: [test_action]

questions:
  risk:
    type: score
    instructions: Rate risk
    criteria: [harm]
  appropriate:
    type: noul
    instructions: Is it appropriate?

rules:
  - name: auto_allow
    when:
      all:
        - appropriate >= 0.8
        - risk <= 3.0
    then: allow
    priority: 10
    reason: Low risk, high confidence

  - name: block_high_risk
    when: risk >= 9.0
    then: block
    priority: 20
    reason: Critical risk

  - name: review_moderate
    when:
      any:
        - risk >= 6.0
        - appropriate < 0.3
    then: human_review
    priority: 30
    reason: Needs human review

default: retry
"""


@pytest.fixture
def engine():
    return PolicyEngine()


@pytest.fixture
def config():
    return load_policy_yaml(BASIC_POLICY)


class TestPolicyEngine:
    def test_first_match_wins(self, engine, config):
        ns = {"appropriate": 0.9, "risk": 2.0}
        result = engine.evaluate(config, ns)
        assert result.disposition == "allow"
        assert result.matched_rule == "auto_allow"

    def test_block_high_risk(self, engine, config):
        ns = {"appropriate": 0.9, "risk": 9.5}
        result = engine.evaluate(config, ns)
        assert result.disposition == "block"
        assert result.matched_rule == "block_high_risk"

    def test_human_review(self, engine, config):
        ns = {"appropriate": 0.1, "risk": 4.0}
        result = engine.evaluate(config, ns)
        assert result.disposition == "human_review"
        assert result.matched_rule == "review_moderate"

    def test_default_fallback(self, engine, config):
        ns = {"appropriate": 0.6, "risk": 4.0}
        result = engine.evaluate(config, ns)
        assert result.disposition == "retry"
        assert result.matched_rule is None

    def test_priority_ordering(self, engine, config):
        # Both auto_allow and block_high_risk could match parts, but priority determines order
        ns = {"appropriate": 0.9, "risk": 1.0}
        result = engine.evaluate(config, ns)
        assert result.disposition == "allow"

    def test_trace_contains_all_rules(self, engine, config):
        ns = {"appropriate": 0.5, "risk": 5.0}
        result = engine.evaluate(config, ns)
        rule_names = [t.rule_name for t in result.traces]
        assert "auto_allow" in rule_names
        assert "block_high_risk" in rule_names
        assert "review_moderate" in rule_names

    def test_trace_shows_matched_and_skipped(self, engine, config):
        ns = {"appropriate": 0.9, "risk": 2.0}
        result = engine.evaluate(config, ns)
        matched = [t for t in result.traces if t.matched]
        skipped = [t for t in result.traces if t.skipped]
        assert len(matched) == 1
        assert matched[0].rule_name == "auto_allow"
        # Only the first match stops evaluation
        assert len(skipped) == 0  # rules after match aren't evaluated

    def test_to_dict(self, engine, config):
        ns = {"appropriate": 0.9, "risk": 2.0}
        result = engine.evaluate(config, ns)
        d = result.to_dict()
        assert d["disposition"] == "allow"
        assert d["matched_rule"] == "auto_allow"
        assert isinstance(d["trace"], list)


class TestPolicyLoader:
    def test_loads_valid_yaml(self):
        config = load_policy_yaml(BASIC_POLICY)
        assert config.name == "Test Policy"
        assert len(config.rules) == 3
        assert len(config.questions) == 2

    def test_rejects_invalid_yaml(self):
        with pytest.raises(PolicyLoadError):
            load_policy_yaml("{{invalid yaml")

    def test_rejects_invalid_disposition(self):
        bad = """
name: Bad
rules:
  - name: bad_rule
    when: "true"
    then: invalid_disposition
"""
        with pytest.raises(PolicyLoadError):
            load_policy_yaml(bad)

    def test_rejects_invalid_question_type(self):
        bad = """
name: Bad
questions:
  test:
    type: invalid
    instructions: test
"""
        with pytest.raises(PolicyLoadError):
            load_policy_yaml(bad)

    def test_default_disposition(self):
        minimal = """
name: Minimal
rules: []
default: block
"""
        config = load_policy_yaml(minimal)
        assert config.default == "block"
