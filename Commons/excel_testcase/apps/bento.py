"""Bento — Excel testcase profile (arm matrix under Testcases/BENTO/arm-*/)."""

from __future__ import annotations

import ast
from typing import List

from Commons.excel_testcase._step_parse import int_arg, parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

BENTO_EXCEL_ACTIONS = [
    "accept_banner",
    "open_cases",
    "select_filter",
    "set_age_range",
    "read_statbar",
    "verify_tab",
    "verify_all_tabs",
    "assert_no_failures",
]

BENTO_ARM_SUBDIRS = ("arm-a", "arm-b", "arm-c", "arm-d")


def _parse_bento_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    def _filter(args: list[ast.AST]) -> StepRow:
        return ("select_filter", str_arg(args[0]), "", str_arg(args[1]))

    def _tab(args: list[ast.AST]) -> StepRow:
        return ("verify_tab", "", str_arg(args[0]), "")

    def _age(args: list[ast.AST]) -> StepRow:
        return ("set_age_range", "", f"{int_arg(args[0])},{int_arg(args[1])}", "")

    return parse_adapter_calls(
        test_fn,
        fixture_name="bento",
        module_consts=module_consts,
        method_to_step={
            "accept_banner": lambda _a: ("accept_banner", "", "", ""),
            "open_cases": lambda _a: ("open_cases", "", "", ""),
            "read_statbar": lambda _a: ("read_statbar", "", "", ""),
            "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
            "select_filter": _filter,
            "verify_tab": _tab,
            "set_age_range": _age,
        },
    )


register_profile(
    ExcelCaseProfile(
        app_key="Bento",
        testcases_dir="BENTO",
        fixture="bento",
        input_files_prefix="InputFiles/BENTO",
        excel_actions=BENTO_EXCEL_ACTIONS,
        parse_test_function=_parse_bento_test_function,
        case_subdirs=BENTO_ARM_SUBDIRS,
    )
)
