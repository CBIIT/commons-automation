"""GC — Excel testcase profile (Data explore under Testcases/GC/studies/)."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

GC_TAB_FROM_PARAMS = {
    "ParticipantsTab": "Participants",
    "SamplesTab": "Samples",
    "FilesTab": "Files",
}

GC_EXCEL_ACTIONS = [
    "accept_banner",
    "click",
    "open_data",
    "open_studies_listing",
    "select_filter",
    "read_statbar",
    "verify_tab",
    "verify_studies_listing",
    "verify_static_data",
    "verify_all_tabs",
    "multi_function",
    "assert_no_failures",
    "click_and_wait",
    "js_click_and_wait",
]

GC_STATIC_DATA_FILE = "GC_StaticData.xlsx"

GC_CASE_SUBDIRS = (
    "studies",
    "study_listing",
    "static",
)


def _open_studies_listing(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.open_studies_listing()


def _verify_studies_listing(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.verify_studies_listing()


def _click_step(app: "BaseApp", page: str, params: str, _flt, _excel) -> None:
    key = f"{page}/{params}".strip("/") if page and params else (params or page).strip()
    if not key:
        raise ValueError("click step needs ObjectRepository key in Page/Params")
    app.click(key)


def _gc_method_to_step() -> dict:
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
        "open_data": lambda _a: ("open_data", "", "", ""),
        "open_studies_listing": lambda _a: ("open_studies_listing", "", "", ""),
        "verify_studies_listing": lambda _a: ("verify_studies_listing", "", "", ""),
        "read_statbar": lambda _a: ("read_statbar", "", "", ""),
        "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
        "select_filter": _filter,
        "verify_tab": _tab,
        "click": _click,
        "verify_static_data": _static,
    }


def _multi_function(app: "BaseApp", _page: str, params: str, _flt: str, _excel: str) -> None:
    tab = GC_TAB_FROM_PARAMS.get(params, params.replace("Tab", "") if params else "")
    tabs = getattr(app, "TABS", {}) or {}
    if tab in tabs:
        app.verify_tab(tab)
    elif params:
        app.verify_tab(params)
    else:
        raise ValueError(f"multi_function step needs tab key in Params, got {params!r}")


def _parse_gc_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    methods = _gc_method_to_step()
    try:
        return parse_adapter_calls(
            test_fn,
            fixture_name="gc",
            module_consts=module_consts,
            method_to_step=methods,
        )
    except ValueError as err:
        if "load_query_file" not in str(err):
            raise
        return parse_adapter_calls(
            test_fn,
            fixture_name="gc",
            module_consts=module_consts,
            method_to_step=methods,
            require_query_file=False,
            default_query_file=GC_STATIC_DATA_FILE,
        )


register_profile(
    ExcelCaseProfile(
        app_key="GC",
        testcases_dir="GC",
        fixture="gc",
        input_files_prefix="InputFiles/GC",
        excel_actions=GC_EXCEL_ACTIONS,
        parse_test_function=_parse_gc_test_function,
        case_subdirs=GC_CASE_SUBDIRS,
        extra_handlers={
            "multi_function": _multi_function,
            "verify_tab_memgraph": _multi_function,
            "open_studies_listing": _open_studies_listing,
            "verify_studies_listing": _verify_studies_listing,
            "click": _click_step,
        },
    )
)
