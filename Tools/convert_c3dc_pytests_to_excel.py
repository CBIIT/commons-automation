"""Convert Testcases/C3DC/test_*.py explore cases to TC*.xlsx Steps workbooks (excel-driven-tests format)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Register C3DC ExcelCaseProfile (side effect).
import Commons.excel_testcase.apps.c3dc  # noqa: F401,E402
from Commons.excel_testcase._step_parse import parse_test_file  # noqa: E402
from Commons.excel_testcase.apps.c3dc import (  # noqa: E402
    C3DC_EXCEL_ACTIONS,
    C3DC_STATIC_DATA_FILE,
    _parse_c3dc_test_function,
)
from Commons.excel_testcase.io import write_excel_case  # noqa: E402

CASE_ROOT = ROOT / "Testcases" / "C3DC"
INPUT_PREFIX = "InputFiles/C3DC"


def _excel_case_name(py_path: Path) -> str:
    """test_TC01_C3DC_foo.py → TC01_C3DC_foo.xlsx"""
    stem = py_path.stem
    if stem.startswith("test_"):
        stem = stem[len("test_") :]
    return f"{stem}.xlsx"


def _input_excel_path(query_file: str) -> str:
    name = Path(query_file.replace("\\", "/")).name
    if name.endswith("_StaticData.xlsx"):
        return f"{INPUT_PREFIX}/{name}"
    return f"{INPUT_PREFIX}/{name}"


def convert_pytest_file(py_path: Path, *, dry_run: bool = False, force: bool = False) -> str:
    out_path = py_path.parent / _excel_case_name(py_path)
    if out_path.exists() and not force:
        return "skip"
    query_file, steps = parse_test_file(py_path, _parse_c3dc_test_function)
    # Runner loads query from row 2; omit load_query_file from step rows.
    steps = [s for s in steps if s[0] != "load_query_file"]
    input_excel = _input_excel_path(query_file or C3DC_STATIC_DATA_FILE)
    if dry_run:
        return "dry-run"
    write_excel_case(
        out_path,
        input_excel=input_excel,
        steps=steps,
        excel_actions=C3DC_EXCEL_ACTIONS,
        dropdown_name="C3DCExcelCaseActions",
    )
    return "written"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Parse only; do not write xlsx")
    parser.add_argument("--force", action="store_true", help="Overwrite existing TC*.xlsx")
    args = parser.parse_args()

    py_files = sorted(CASE_ROOT.rglob("test_*.py"))
    if not py_files:
        raise SystemExit(f"No test_*.py under {CASE_ROOT}")

    counts = {"written": 0, "skip": 0, "dry-run": 0, "error": 0}
    for py_path in py_files:
        try:
            status = convert_pytest_file(py_path, dry_run=args.dry_run, force=args.force)
            counts[status] = counts.get(status, 0) + 1
            if status != "skip":
                print(status, py_path.relative_to(ROOT))
        except Exception as err:
            counts["error"] += 1
            print("ERROR", py_path.relative_to(ROOT), err)

    print(
        f"Done: {counts.get('written', 0)} written, {counts.get('skip', 0)} skipped, "
        f"{counts.get('error', 0)} errors"
    )
    if counts.get("error"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
