"""Per-app Excel testcase configuration (runtime + Python→Excel conversion)."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

StepRow = Tuple[str, str, str, str]  # action, page, params, filter

ParseFn = Callable[[ast.FunctionDef, Dict[str, str]], Tuple[str, List[StepRow]]]


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
    parse_test_function: optional AST parser (legacy; cases are authored as TC*.xlsx)
    """

    app_key: str
    testcases_dir: str
    fixture: str
    input_files_prefix: str
    excel_actions: Sequence[str]
    parse_test_function: ParseFn
    extra_handlers: Dict[str, Callable] = field(default_factory=dict)
    case_subdirs: Sequence[str] = ("studies",)

    def query_workbook_row2(self, query_filename: str) -> str:
        return f"{self.input_files_prefix.rstrip('/')}/{query_filename}"

    def studies_root(self, repo_root: Path) -> Path:
        """Primary case folder (legacy name; first entry in case_subdirs)."""
        return repo_root / "Testcases" / self.testcases_dir / self.case_subdirs[0]

    def case_file_roots(self, repo_root: Path) -> List[Path]:
        """Directories to scan for test_*.py / TC*.xlsx (e.g. studies/ or arm-a/)."""
        base = repo_root / "Testcases" / self.testcases_dir
        return [base / sub for sub in self.case_subdirs]
