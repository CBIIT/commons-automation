"""C3DC — Excel testcase profile (Explore Participants under Testcases/C3DC/studies/)."""

from __future__ import annotations

import ast
from typing import List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

C3DC_EXCEL_ACTIONS = [
    "accept_banner",
    "open_explore",
    "select_filter",
    "read_statbar",
    "verify_tab",
    "verify_all_tabs",
    "assert_no_failures",
]


def _parse_c3dc_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    def _filter(args: list[ast.AST]) -> StepRow:
        return ("select_filter", str_arg(args[0]), "", str_arg(args[1]))

    def _tab(args: list[ast.AST]) -> StepRow:
        return ("verify_tab", "", str_arg(args[0]), "")

    return parse_adapter_calls(
        test_fn,
        fixture_name="c3dc",
        module_consts=module_consts,
        method_to_step={
            "accept_banner": lambda _a: ("accept_banner", "", "", ""),
            "open_explore": lambda _a: ("open_explore", "", "", ""),
            "read_statbar": lambda _a: ("read_statbar", "", "", ""),
            "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
            "select_filter": _filter,
            "verify_tab": _tab,
        },
    )


register_profile(
    ExcelCaseProfile(
        app_key="C3DC",
        testcases_dir="C3DC",
        fixture="c3dc",
        input_files_prefix="InputFiles/C3DC",
        excel_actions=C3DC_EXCEL_ACTIONS,
        parse_test_function=_parse_c3dc_test_function,
    )
)
