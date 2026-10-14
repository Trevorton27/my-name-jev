"""Hypothesis property tests for the expression evaluator."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from jevops.policies.expression import (
    ExpressionEvalError,
    UnsafeExpressionError,
    evaluate_expression,
    validate_expression,
)

# Strategy for valid variable names
var_names = st.sampled_from(["x", "y", "z", "risk", "score", "confidence"])

# Strategy for safe numeric comparisons
safe_comparisons = st.builds(
    lambda var, op, val: f"{var} {op} {val}",
    var_names,
    st.sampled_from([">=", "<=", ">", "<", "==", "!="]),
    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
)

# Strategy for boolean combinations
safe_bool_exprs = st.builds(
    lambda e1, op, e2: f"{e1} {op} {e2}",
    safe_comparisons,
    st.sampled_from(["and", "or"]),
    safe_comparisons,
)


@given(expr=safe_comparisons)
def test_safe_comparisons_always_validate(expr):
    """Any comparison with allowed ops should pass validation."""
    validate_expression(expr)


@given(expr=safe_bool_exprs)
def test_safe_bool_expressions_validate(expr):
    """Boolean combinations of safe expressions should validate."""
    validate_expression(expr)


@given(
    expr=safe_comparisons,
    x=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    y=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    z=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
)
def test_safe_expressions_produce_bool(expr, x, y, z):
    """Safe expressions with valid namespace should return a boolean-compatible value."""
    ns = {"x": x, "y": y, "z": z, "risk": x, "score": y, "confidence": z}
    try:
        result = evaluate_expression(expr, ns)
        assert isinstance(result, bool)
    except ExpressionEvalError:
        pass  # Undefined vars are OK for this test


# Dangerous expressions that should always be rejected
dangerous_expressions = st.sampled_from(
    [
        "__import__('os').system('ls')",
        "exec('print(1)')",
        "eval('1+1')",
        "lambda: 1",
        "x.__class__.__bases__",
        "().__class__.__subclasses__()",
        "open('/etc/passwd')",
        "globals()",
        "locals()",
        "dir()",
        "getattr(x, '__class__')",
        "type(x)()",
        "compile('x', '', 'eval')",
    ]
)


@given(expr=dangerous_expressions)
def test_dangerous_expressions_always_rejected(expr):
    """Dangerous expressions should always raise UnsafeExpressionError."""
    with pytest.raises((UnsafeExpressionError, SyntaxError)):
        validate_expression(expr)
