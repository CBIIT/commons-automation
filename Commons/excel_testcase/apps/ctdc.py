"""CTDC — Excel testcase profile (Explore under Testcases/CTDC/studies/)."""

from __future__ import annotations

import ast
from typing import List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

CTDC_EXCEL_ACTIONS = [
    "accept_banner",
    "open_explore",
    "select_study",
    "select_filter",
    "read_statbar",
    "verify_tab",
    "verify_all_tabs",
    "assert_no_failures",
]


def _parse_ctdc_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    def _filter(args: list[ast.AST]) -> StepRow:
        return ("select_filter", str_arg(args[0]), "", str_arg(args[1]))

    def _tab(args: list[ast.AST]) -> StepRow:
        return ("verify_tab", "", str_arg(args[0]), "")

    return parse_adapter_calls(
        test_fn,
        fixture_name="ctdc",
        module_consts=module_consts,
        method_to_step={
            "accept_banner": lambda _a: ("accept_banner", "", "", ""),
            "open_explore": lambda _a: ("open_explore", "", "", ""),
            "select_study": lambda a: ("select_study", "", str_arg(a[0]), ""),
            "read_statbar": lambda _a: ("read_statbar", "", "", ""),
            "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
            "select_filter": _filter,
            "verify_tab": _tab,
        },
    )


register_profile(
    ExcelCaseProfile(
        app_key="CTDC",
        testcases_dir="CTDC",
        fixture="ctdc",
        input_files_prefix="InputFiles/CTDC",
        excel_actions=CTDC_EXCEL_ACTIONS,
        parse_test_function=_parse_ctdc_test_function,
    )
)
