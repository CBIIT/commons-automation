"""Per-app Excel testcase configuration (runtime + Python→Excel conversion)."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

StepRow = Tuple[str, str, str, str]  # action, page, params, filter

ParseFn = Callable[[ast.FunctionDef], Tuple[str, List[StepRow]]]


@dataclass(frozen=True)
class ExcelCaseProfile:
    """
    All Excel testcase behavior for one portal.

    app_key: matches BaseApp.NAME (e.g. GC, CTDC).
    testcases_dir: folder under Testcases/ (usually same as app_key).
    fixture: pytest fixture name (gc, ctdc, …).
    input_files_prefix: row-2 path prefix, e.g. InputFiles/GC/
    excel_actions: Steps sheet Action dropdown values for this app only.
    extra_handlers: action name → runner handler (app-specific steps).
    parse_test_function: AST parser for Tools/convert_study_tests_to_excel.py
    """

    app_key: str
    testcases_dir: str
    fixture: str
    input_files_prefix: str
    excel_actions: Sequence[str]
    parse_test_function: ParseFn
    extra_handlers: Dict[str, Callable] = field(default_factory=dict)

    def query_workbook_row2(self, query_filename: str) -> str:
        return f"{self.input_files_prefix.rstrip('/')}/{query_filename}"

    def studies_root(self, repo_root: Path) -> Path:
        return repo_root / "Testcases" / self.testcases_dir / "studies"
