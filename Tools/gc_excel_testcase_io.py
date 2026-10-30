"""Deprecated: use Commons.excel_testcase.io.write_excel_case and app profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from Commons.excel_testcase.apps.gc import GC_EXCEL_ACTIONS
from Commons.excel_testcase.io import STEPS_HEADER, write_excel_case
from Commons.excel_testcase.profile import StepRow

HEADER = STEPS_HEADER
EXCEL_CASE_ACTIONS = GC_EXCEL_ACTIONS
GC_EXCEL_ACTIONS = GC_EXCEL_ACTIONS


def write_gc_excel_case(
    out_path: Path,
    *,
    input_excel: str,
    steps: Sequence[StepRow],
) -> None:
    write_excel_case(
        out_path,
        input_excel=input_excel,
        steps=steps,
        excel_actions=GC_EXCEL_ACTIONS,
    )
