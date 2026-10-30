#!/usr/bin/env python3
"""
Convert Testcases/<APP>/studies/**/test_*.py to TC*.xlsx using that app's ExcelCaseProfile.

Usage:
  python3 Tools/convert_study_tests_to_excel.py GC
  python3 Tools/convert_study_tests_to_excel.py CTDC --keep-py

Add a new app: Commons/excel_testcase/apps/<app>.py (register_profile), then run this tool.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Commons.excel_testcase.io import write_excel_case  # noqa: E402
from Commons.excel_testcase.registry import get_profile  # noqa: E402
from Commons.excel_testcase._step_parse import parse_test_file  # noqa: E402


def convert_app(app_key: str, *, delete_py: bool = True) -> tuple[int, int, list[str]]:
    profile = get_profile(app_key)
    studies = profile.studies_root(ROOT)
    if not studies.is_dir():
        raise FileNotFoundError(f"Studies folder not found: {studies}")

    written = 0
    deleted = 0
    errors: list[str] = []
    for py_path in sorted(studies.rglob("test_*.py")):
        try:
            query_file, steps = parse_test_file(py_path, profile.parse_test_function)
            stem = Path(query_file).stem
            xlsx_path = py_path.parent / f"{stem}.xlsx"
            input_rel = profile.query_workbook_row2(query_file)
            write_excel_case(
                xlsx_path,
                input_excel=input_rel,
                steps=steps,
                excel_actions=profile.excel_actions,
            )
            written += 1
            if delete_py:
                py_path.unlink()
                deleted += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"{py_path}: {e}")
    return written, deleted, errors


def main() -> int:
    argv = [a for a in sys.argv[1:] if a.startswith("-")]
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print("Usage: convert_study_tests_to_excel.py <APP_KEY> [--keep-py]", file=sys.stderr)
        print("Example: convert_study_tests_to_excel.py GC", file=sys.stderr)
        return 2
    keep_py = "--keep-py" in argv
    app_key = args[0]
    written, deleted, errors = convert_app(app_key, delete_py=not keep_py)
    print(f"[{app_key}] Wrote {written} Excel test case(s)")
    if not keep_py:
        print(f"[{app_key}] Removed {deleted} Python test file(s)")
    if errors:
        print(f"{len(errors)} error(s):", file=sys.stderr)
        for line in errors[:30]:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
