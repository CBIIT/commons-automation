"""
Execute Excel testcase Steps sheets (legacy import path).

Implementation: Commons/excel_testcase/runner.py and per-app profiles under
Commons/excel_testcase/apps/.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Public API (re-export)
# ---------------------------------------------------------------------------

from Commons.excel_testcase.runner import run_testcase_excel

__all__ = ["run_testcase_excel"]
