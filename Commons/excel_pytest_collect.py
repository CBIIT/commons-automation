"""Collect TC*.xlsx under Testcases/<APP>/studies/ as pytest tests (excel mode only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from Commons.excel_test_runner import run_testcase_excel
from Commons.settings import get_test_case_source

_APP_FIXTURE = {
    "GC": "gc",
    "C3DC": "c3dc",
    "ICDC": "icdc",
    "CTDC": "ctdc",
    "INS": "ins",
    "BENTO": "bento",
    "Bento": "bento",
    "CCDI": "ccdi",
}


def app_fixture_for(case_path: Path) -> str:
    parts = case_path.parts
    try:
        i = parts.index("Testcases")
        app_dir = parts[i + 1]
    except (ValueError, IndexError) as e:
        raise ValueError(f"Cannot infer app from Excel path: {case_path}") from e
    fix = _APP_FIXTURE.get(app_dir) or _APP_FIXTURE.get(app_dir.upper())
    if not fix:
        raise ValueError(f"No pytest fixture mapped for Testcases/{app_dir}/ ({case_path})")
    return fix


def _make_test_fn(case_path: Path, app_fixture: str):
    def test_fn(request):
        app = request.getfixturevalue(app_fixture)
        run_testcase_excel(app, case_path)

    test_fn.__name__ = case_path.stem
    test_fn = getattr(pytest.mark, app_fixture)(test_fn)
    test_fn = pytest.mark.regression(test_fn)
    if case_path.name.startswith("TC01_"):
        test_fn = pytest.mark.smoke(test_fn)
    return test_fn


class ExcelCaseFile(pytest.File):
    """One TC*.xlsx file → one pytest test."""

    def collect(self):
        case_path = Path(str(self.path))
        app_fixture = app_fixture_for(case_path)
        fn = _make_test_fn(case_path, app_fixture)
        yield pytest.Function.from_parent(self, name=case_path.stem, callobj=fn)


def pytest_collect_file(file_path, parent):
    if get_test_case_source() != "excel":
        return None
    path = Path(str(file_path))
    if path.suffix.lower() != ".xlsx" or not path.name.startswith("TC"):
        return None
    if "studies" not in path.parts:
        return None
    return ExcelCaseFile.from_parent(parent, path=path)
