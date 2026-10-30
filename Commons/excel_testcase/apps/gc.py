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
    "open_data",
    "select_filter",
    "read_statbar",
    "verify_tab",
    "verify_all_tabs",
    "multi_function",
    "assert_no_failures",
    "click_and_wait",
    "js_click_and_wait",
]


def _multi_function(app: "BaseApp", _page: str, params: str, _flt: str, _excel: str) -> None:
    tab = GC_TAB_FROM_PARAMS.get(params, params.replace("Tab", "") if params else "")
    tabs = getattr(app, "TABS", {}) or {}
    if tab in tabs:
        app.verify_tab(tab)
    elif params:
        app.verify_tab(params)
    else:
        raise ValueError(f"multi_function step needs tab key in Params, got {params!r}")


def _parse_gc_test_function(test_fn: ast.FunctionDef) -> tuple[str, List[StepRow]]:
    def _filter(args: list[ast.AST]) -> StepRow:
        return ("select_filter", str_arg(args[0]), "", str_arg(args[1]))

    def _tab(args: list[ast.AST]) -> StepRow:
        return ("verify_tab", "", str_arg(args[0]), "")

    return parse_adapter_calls(
        test_fn,
        fixture_name="gc",
        method_to_step={
            "accept_banner": lambda _a: ("accept_banner", "", "", ""),
            "open_data": lambda _a: ("open_data", "", "", ""),
            "read_statbar": lambda _a: ("read_statbar", "", "", ""),
            "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
            "select_filter": _filter,
            "verify_tab": _tab,
        },
    )


register_profile(
    ExcelCaseProfile(
        app_key="GC",
        testcases_dir="GC",
        fixture="gc",
        input_files_prefix="InputFiles/GC",
        excel_actions=GC_EXCEL_ACTIONS,
        parse_test_function=_parse_gc_test_function,
        extra_handlers={
            "multi_function": _multi_function,
            "verify_tab_memgraph": _multi_function,
        },
    )
)
