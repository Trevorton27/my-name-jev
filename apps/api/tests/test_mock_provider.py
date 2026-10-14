import pytest

from jevops.jev.mock_provider import MockProvider
from jevops.jev.types import QuestionType, TypedQuestion


@pytest.fixture
def provider():
    return MockProvider(profile="balanced")


@pytest.fixture
def questions():
    return {
        "appropriate": TypedQuestion(
            type=QuestionType.NOUL,
            instructions="Is this action appropriate?",
        ),
        "route": TypedQuestion(
            type=QuestionType.CHOICE,
            instructions="Recommended route?",
            criteria={"allow": "Safe", "block": "Unsafe"},
        ),
        "risk": TypedQuestion(
            type=QuestionType.SCORE,
            instructions="Risk level?",
            criteria=["harm", "reversibility"],
        ),
    }


@pytest.mark.asyncio
async def test_mock_returns_all_question_types(provider, questions):
    result = await provider.evaluate({"action": "test"}, questions)
    assert len(result.judgments) == 3
    types = {j.question_type for j in result.judgments}
    assert types == {QuestionType.NOUL, QuestionType.CHOICE, QuestionType.SCORE}


@pytest.mark.asyncio
async def test_mock_deterministic(provider, questions):
    state = {"action": "deploy", "target": "prod"}
    r1 = await provider.evaluate(state, questions)
    r2 = await provider.evaluate(state, questions)
    for j1, j2 in zip(r1.judgments, r2.judgments):
        assert j1.value == j2.value


@pytest.mark.asyncio
async def test_noul_in_range(provider):
    q = {"test": TypedQuestion(type=QuestionType.NOUL, instructions="test")}
    result = await provider.evaluate({"x": 1}, q)
    val = result.judgments[0].value
    assert 0.0 <= val <= 1.0


@pytest.mark.asyncio
async def test_choice_has_probabilities(provider):
    q = {
        "test": TypedQuestion(
            type=QuestionType.CHOICE,
            instructions="test",
            criteria={"a": "A", "b": "B", "c": "C"},
        )
    }
    result = await provider.evaluate({"x": 1}, q)
    j = result.judgments[0]
    assert j.probabilities is not None
    assert abs(sum(j.probabilities.values()) - 1.0) < 0.01
    assert j.value in j.probabilities


@pytest.mark.asyncio
async def test_score_in_range(provider):
    q = {"test": TypedQuestion(type=QuestionType.SCORE, instructions="test", criteria=["a"])}
    result = await provider.evaluate({"x": 1}, q)
    val = result.judgments[0].value
    assert 1.0 <= val <= 10.0
