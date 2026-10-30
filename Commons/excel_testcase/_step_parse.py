"""Shared AST helpers for Python test → Excel Steps conversion."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Tuple

from Commons.excel_testcase.profile import StepRow


def str_arg(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise ValueError(f"Expected string literal, got {ast.dump(node)}")


def parse_adapter_calls(
    test_fn: ast.FunctionDef,
    *,
    fixture_name: str,
    method_to_step: dict[str, callable],
) -> Tuple[str, List[StepRow]]:
    query_name = ""
    steps: List[StepRow] = []
    for stmt in test_fn.body:
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            continue
        call = stmt.value
        if not isinstance(call.func, ast.Attribute):
            continue
        if not isinstance(call.func.value, ast.Name) or call.func.value.id != fixture_name:
            continue
        method = call.func.attr
        args = call.args
        if method == "load_query_file":
            query_name = str_arg(args[0])
            continue
        if method not in method_to_step:
            raise ValueError(f"Unsupported {fixture_name}.{method}()")
        step = method_to_step[method](args)
        if step is not None:
            if isinstance(step, tuple):
                steps.append(step)
            else:
                steps.extend(step)
    if not query_name:
        raise ValueError(f"No {fixture_name}.load_query_file(...) found")
    if not steps or steps[-1][0] != "assert_no_failures":
        raise ValueError("Expected assert_no_failures at end")
    return query_name, steps


def parse_test_file(py_path: Path, parse_fn) -> Tuple[str, List[StepRow]]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            return parse_fn(node)
    raise ValueError("No test_* function found")
