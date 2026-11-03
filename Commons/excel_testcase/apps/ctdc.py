"""CTDC — Excel testcase profile (Explore + static pages under Testcases/CTDC/)."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

CTDC_EXCEL_ACTIONS = [
    "accept_banner",
    "click",
    "open_explore",
    "select_study",
    "select_filter",
    "read_statbar",
    "verify_tab",
    "verify_static_data",
    "verify_all_tabs",
    "assert_no_failures",
]

CTDC_STATIC_DATA_FILE = "TC01_CTDC_StaticData.xlsx"

CTDC_CASE_SUBDIRS = (
    "studies",
    "static",
)


def _click_step(app: "BaseApp", page: str, params: str, _flt, _excel) -> None:
    key = f"{page}/{params}".strip("/") if page and params else (params or page).strip()
    if not key:
        raise ValueError("click step needs ObjectRepository key in Page/Params")
    app.click(key)


def _ctdc_method_to_step() -> dict:
    def _filter(args: list[ast.AST]) -> StepRow:
        return ("select_filter", str_arg(args[0]), "", str_arg(args[1]))

    def _tab(args: list[ast.AST]) -> StepRow:
        return ("verify_tab", "", str_arg(args[0]), "")

    def _click(args: list[ast.AST]) -> StepRow:
        key = str_arg(args[0])
        if "/" in key:
            page, obj = key.split("/", 1)
            return ("click", page, obj, "")
        return ("click", "", key, "")

    def _static(args: list[ast.AST]) -> StepRow:
        return ("verify_static_data", "", str_arg(args[0]), "")

    return {
        "accept_banner": lambda _a: ("accept_banner", "", "", ""),
        "open_explore": lambda _a: ("open_explore", "", "", ""),
        "select_study": lambda a: ("select_study", "", str_arg(a[0]), ""),
        "read_statbar": lambda _a: ("read_statbar", "", "", ""),
        "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
        "select_filter": _filter,
        "verify_tab": _tab,
        "click": _click,
        "verify_static_data": _static,
    }


def _parse_ctdc_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    methods = _ctdc_method_to_step()
    try:
        return parse_adapter_calls(
            test_fn,
            fixture_name="ctdc",
            module_consts=module_consts,
            method_to_step=methods,
        )
    except ValueError as err:
        if "load_query_file" not in str(err):
            raise
        return parse_adapter_calls(
            test_fn,
            fixture_name="ctdc",
            module_consts=module_consts,
            method_to_step=methods,
            require_query_file=False,
            default_query_file=CTDC_STATIC_DATA_FILE,
        )


register_profile(
    ExcelCaseProfile(
        app_key="CTDC",
        testcases_dir="CTDC",
        fixture="ctdc",
        input_files_prefix="InputFiles/CTDC",
        excel_actions=CTDC_EXCEL_ACTIONS,
        parse_test_function=_parse_ctdc_test_function,
        case_subdirs=CTDC_CASE_SUBDIRS,
        extra_handlers={"click": _click_step},
    )
)
