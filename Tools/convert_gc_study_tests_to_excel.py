#!/usr/bin/env python3
"""
Convert Testcases/GC/studies/**/test_*.py explore tests to TC*.xlsx and remove the .py files.

Does not touch Testcases/GC/static or study_listing.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIES = ROOT / "Testcases" / "GC" / "studies"

sys.path.insert(0, str(ROOT))
from Tools.gc_excel_testcase_io import write_gc_excel_case  # noqa: E402


def _str_arg(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise ValueError(f"Expected string literal, got {ast.dump(node)}")


def _parse_gc_calls(test_fn: ast.FunctionDef) -> tuple[str, list[tuple[str, str, str, str]]]:
    query_name = ""
    steps: list[tuple[str, str, str, str]] = []
    for stmt in test_fn.body:
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            continue
        call = stmt.value
        if not isinstance(call.func, ast.Attribute):
            continue
        if not isinstance(call.func.value, ast.Name) or call.func.value.id != "gc":
            continue
        method = call.func.attr
        args = call.args
        if method == "load_query_file":
            query_name = _str_arg(args[0])
            continue
        if method == "accept_banner":
            steps.append(("accept_banner", "", "", ""))
        elif method == "open_data":
            steps.append(("open_data", "", "", ""))
        elif method == "read_statbar":
            steps.append(("read_statbar", "", "", ""))
        elif method == "assert_no_failures":
            steps.append(("assert_no_failures", "", "", ""))
        elif method == "select_filter":
            group, value = _str_arg(args[0]), _str_arg(args[1])
            steps.append(("select_filter", group, "", value))
        elif method == "verify_tab":
            tab = _str_arg(args[0])
            steps.append(("verify_tab", "", tab, ""))
        else:
            raise ValueError(f"Unsupported gc.{method}()")
    if not query_name:
        raise ValueError("No gc.load_query_file(...) found")
    if not steps or steps[-1][0] != "assert_no_failures":
        raise ValueError("Expected assert_no_failures at end")
    return query_name, steps


def _parse_test_file(py_path: Path) -> tuple[str, list[tuple[str, str, str, str]]]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            return _parse_gc_calls(node)
    raise ValueError("No test_* function found")


def convert_all(*, delete_py: bool = True) -> tuple[int, int, list[str]]:
    written = 0
    deleted = 0
    errors: list[str] = []
    for py_path in sorted(STUDIES.rglob("test_*.py")):
        try:
            query_file, steps = _parse_test_file(py_path)
            stem = Path(query_file).stem
            xlsx_path = py_path.parent / f"{stem}.xlsx"
            input_rel = f"InputFiles/GC/{query_file}"
            write_gc_excel_case(xlsx_path, input_excel=input_rel, steps=steps)
            written += 1
            if delete_py:
                py_path.unlink()
                deleted += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"{py_path}: {e}")
    return written, deleted, errors


def main() -> int:
    keep_py = "--keep-py" in sys.argv
    written, deleted, errors = convert_all(delete_py=not keep_py)
    print(f"Wrote {written} Excel test case(s)")
    if not keep_py:
        print(f"Removed {deleted} Python test file(s)")
    if errors:
        print(f"{len(errors)} error(s):", file=sys.stderr)
        for line in errors[:30]:
            print(f"  {line}", file=sys.stderr)
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
