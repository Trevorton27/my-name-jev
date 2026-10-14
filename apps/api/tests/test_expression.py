import pytest

from jevops.policies.expression import (
    ExpressionEvalError,
    UnsafeExpressionError,
    evaluate_expression,
    validate_expression,
)


class TestValidation:
    def test_allows_comparisons(self):
        validate_expression("x >= 0.5")
        validate_expression("x < 10")
        validate_expression("x == 'hello'")
        validate_expression("x != 'bad'")

    def test_allows_boolean_ops(self):
        validate_expression("x > 0 and y < 10")
        validate_expression("x > 0 or y < 10")
        validate_expression("not x")

    def test_allows_in_operator(self):
        validate_expression("x in ['a', 'b', 'c']")
        validate_expression("x not in ['bad']")

    def test_rejects_function_calls(self):
        with pytest.raises(UnsafeExpressionError, match=r"Disallowed node.*Call"):
            validate_expression("len(x)")

    def test_rejects_import(self):
        with pytest.raises(UnsafeExpressionError):
            validate_expression("__import__('os')")

    def test_rejects_lambda(self):
        with pytest.raises(UnsafeExpressionError, match=r"Disallowed node.*Lambda"):
            validate_expression("lambda: 1")

    def test_rejects_dunder_attribute(self):
        with pytest.raises(UnsafeExpressionError, match="Dunder"):
            validate_expression("x.__class__")

    def test_rejects_exec_eval(self):
        with pytest.raises(UnsafeExpressionError):
            validate_expression("exec('print(1)')")
        with pytest.raises(UnsafeExpressionError):
            validate_expression("eval('1+1')")


class TestEvaluation:
    def test_simple_comparison(self):
        assert evaluate_expression("x >= 0.5", {"x": 0.7}) is True
        assert evaluate_expression("x >= 0.5", {"x": 0.3}) is False

    def test_equality(self):
        assert evaluate_expression("x == 'allow'", {"x": "allow"}) is True
        assert evaluate_expression("x == 'allow'", {"x": "block"}) is False

    def test_and(self):
        ns = {"x": 0.8, "y": 3.0}
        assert evaluate_expression("x >= 0.5 and y <= 5.0", ns) is True
        assert evaluate_expression("x >= 0.9 and y <= 5.0", ns) is False

    def test_or(self):
        ns = {"x": 0.2, "y": 8.0}
        assert evaluate_expression("x >= 0.5 or y >= 7.0", ns) is True

    def test_not(self):
        assert evaluate_expression("not x", {"x": False}) is True
        assert evaluate_expression("not x", {"x": True}) is False

    def test_in_list(self):
        assert evaluate_expression("x in ['a', 'b']", {"x": "a"}) is True
        assert evaluate_expression("x in ['a', 'b']", {"x": "c"}) is False

    def test_not_in(self):
        assert evaluate_expression("x not in ['bad']", {"x": "good"}) is True

    def test_chained_comparison(self):
        assert evaluate_expression("1 <= x <= 10", {"x": 5}) is True
        assert evaluate_expression("1 <= x <= 10", {"x": 11}) is False

    def test_undefined_variable(self):
        with pytest.raises(ExpressionEvalError, match="Undefined"):
            evaluate_expression("missing > 0", {})

    def test_numeric_types(self):
        assert evaluate_expression("x > 0.5", {"x": 0.8}) is True
        assert evaluate_expression("x > 0.5", {"x": 0}) is False

    def test_constant_expression(self):
        assert evaluate_expression("True", {}) is True
        assert evaluate_expression("False", {}) is False
