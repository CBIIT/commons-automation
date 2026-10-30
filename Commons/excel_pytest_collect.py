"""
Collect TC*.xlsx under Testcases/<APP>/studies/ as pytest tests (excel mode only).

Requires framework.test_case_source: excel. Per-app profiles: Commons/excel_testcase/apps/.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from Commons.excel_testcase.runner import run_testcase_excel
from Commons.excel_testcase.registry import fixture_for_case_path, profile_for_case_path
from Commons.settings import get_test_case_source

# ---------------------------------------------------------------------------
# Test function factory (fixture + markers)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Pytest collector (one TC*.xlsx → one test function)
# ---------------------------------------------------------------------------


class ExcelCaseFile(pytest.File):
    """One TC*.xlsx file → one pytest test."""

    def collect(self):
        case_path = Path(str(self.path))
        app_fixture = fixture_for_case_path(case_path)
        fn = _make_test_fn(case_path, app_fixture)
        yield pytest.Function.from_parent(self, name=case_path.stem, callobj=fn)


# ---------------------------------------------------------------------------
# pytest_collect_file hook
# ---------------------------------------------------------------------------


def pytest_collect_file(file_path, parent):
    if get_test_case_source() != "excel":
        return None
    path = Path(str(file_path))
    if path.suffix.lower() != ".xlsx" or not path.name.startswith("TC"):
        return None
    if "studies" not in path.parts:
        return None
    # Only collect apps that have an ExcelCaseProfile (extend apps/*.py for new portals).
    if profile_for_case_path(path) is None:
        return None
    return ExcelCaseFile.from_parent(parent, path=path)
