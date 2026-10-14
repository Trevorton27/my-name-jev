from __future__ import annotations

import ast
import operator
from typing import Any

ALLOWED_NODES = {
    ast.Expression,
    ast.Compare,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.Not,
    ast.UnaryOp,
    ast.USub,
    ast.Constant,
    ast.Name,
    ast.Attribute,
    ast.Load,
    # Comparison ops
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
    # Containers for 'in' checks
    ast.List,
    ast.Tuple,
}

COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


class UnsafeExpressionError(Exception):
    pass


class ExpressionEvalError(Exception):
    pass


def validate_expression(expr: str) -> None:
    """Validate that an expression only contains allowed AST nodes."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise UnsafeExpressionError(f"Syntax error in expression: {e}") from e

    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise UnsafeExpressionError(f"Disallowed node type: {type(node).__name__} in expression: {expr}")
        # Block dunder attribute access
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise UnsafeExpressionError(f"Dunder attribute access not allowed: {node.attr}")


def evaluate_expression(expr: str, namespace: dict[str, Any]) -> Any:
    """Safely evaluate an expression against a namespace."""
    validate_expression(expr)
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree.body, namespace)


def _eval_node(node: ast.expr, ns: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id not in ns:
            raise ExpressionEvalError(f"Undefined variable: {node.id}")
        return ns[node.id]

    if isinstance(node, ast.Attribute):
        obj = _eval_node(node.value, ns)
        if node.attr.startswith("__"):
            raise UnsafeExpressionError(f"Dunder access blocked: {node.attr}")
        try:
            return getattr(obj, node.attr)
        except AttributeError as e:
            raise ExpressionEvalError(f"Attribute not found: {node.attr}") from e

    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not _eval_node(node.operand, ns)
        if isinstance(node.op, ast.USub):
            return -_eval_node(node.operand, ns)

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(_eval_node(v, ns) for v in node.values)
        if isinstance(node.op, ast.Or):
            return any(_eval_node(v, ns) for v in node.values)

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, ns)
        for op_node, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, ns)
            if isinstance(op_node, ast.In):
                if left not in right:
                    return False
            elif isinstance(op_node, ast.NotIn):
                if left in right:
                    return False
            else:
                op_func = COMPARE_OPS.get(type(op_node))
                if op_func is None:
                    raise ExpressionEvalError(f"Unsupported comparison: {type(op_node).__name__}")
                if not op_func(left, right):
                    return False
            left = right
        return True

    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval_node(elt, ns) for elt in node.elts]

    raise ExpressionEvalError(f"Unsupported node: {type(node).__name__}")
