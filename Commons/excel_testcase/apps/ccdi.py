"""CCDI Hub — Excel testcase profile (static pages under Testcases/CCDI/static/)."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

CCDI_EXCEL_ACTIONS = [
    "accept_banner",
    "click",
    "verify_static_data",
    "assert_no_failures",
]

CCDI_STATIC_DATA_FILE = "TC01_CCDI_StaticData.xlsx"

CCDI_CASE_SUBDIRS = ("static",)


def _click_step(app: "BaseApp", page: str, params: str, _flt, _excel) -> None:
    key = f"{page}/{params}".strip("/") if page and params else (params or page).strip()
    if not key:
        raise ValueError("click step needs ObjectRepository key in Page/Params")
    app.click(key)


def _ccdi_method_to_step() -> dict:
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
        "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
        "click": _click,
        "verify_static_data": _static,
    }


def _parse_ccdi_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    methods = _ccdi_method_to_step()
    try:
        return parse_adapter_calls(
            test_fn,
            fixture_name="ccdi",
            module_consts=module_consts,
            method_to_step=methods,
        )
    except ValueError as err:
        if "load_query_file" not in str(err):
            raise
        return parse_adapter_calls(
            test_fn,
            fixture_name="ccdi",
            module_consts=module_consts,
            method_to_step=methods,
            require_query_file=False,
            default_query_file=CCDI_STATIC_DATA_FILE,
        )


register_profile(
    ExcelCaseProfile(
        app_key="CCDI",
        testcases_dir="CCDI",
        fixture="ccdi",
        input_files_prefix="InputFiles/CCDI",
        excel_actions=CCDI_EXCEL_ACTIONS,
        parse_test_function=_parse_ccdi_test_function,
        case_subdirs=CCDI_CASE_SUBDIRS,
        extra_handlers={"click": _click_step},
    )
)
