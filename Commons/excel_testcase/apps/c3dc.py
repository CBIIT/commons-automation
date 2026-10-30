"""C3DC — Excel testcase profile (Explore Participants + static pages)."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

C3DC_EXCEL_ACTIONS = [
    "accept_banner",
    "open_explore",
    "open_studies_listing",
    "select_filter",
    "read_statbar",
    "verify_tab",
    "verify_studies_listing",
    "goto",
    "verify_static_data",
    "verify_all_tabs",
    "assert_no_failures",
]

C3DC_STATIC_DATA_FILE = "C3DC_StaticData.xlsx"

C3DC_CASE_SUBDIRS = (
    "studies",
    "study_listing",
    "static",
)


def _open_studies_listing(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.open_studies_listing()


def _verify_studies_listing(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.verify_studies_listing()


def _c3dc_method_to_step() -> dict:
    def _filter(args: list[ast.AST]) -> StepRow:
        return ("select_filter", str_arg(args[0]), "", str_arg(args[1]))

    def _tab(args: list[ast.AST]) -> StepRow:
        return ("verify_tab", "", str_arg(args[0]), "")

    def _goto(args: list[ast.AST]) -> StepRow:
        return ("goto", "", str_arg(args[0]), "")

    def _static(args: list[ast.AST]) -> StepRow:
        return ("verify_static_data", "", str_arg(args[0]), "")

    return {
        "accept_banner": lambda _a: ("accept_banner", "", "", ""),
        "open_explore": lambda _a: ("open_explore", "", "", ""),
        "open_studies_listing": lambda _a: ("open_studies_listing", "", "", ""),
        "verify_studies_listing": lambda _a: ("verify_studies_listing", "", "", ""),
        "read_statbar": lambda _a: ("read_statbar", "", "", ""),
        "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
        "select_filter": _filter,
        "verify_tab": _tab,
        "goto": _goto,
        "verify_static_data": _static,
    }


def _parse_c3dc_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    methods = _c3dc_method_to_step()
    try:
        return parse_adapter_calls(
            test_fn,
            fixture_name="c3dc",
            module_consts=module_consts,
            method_to_step=methods,
        )
    except ValueError as err:
        if "load_query_file" not in str(err):
            raise
        return parse_adapter_calls(
            test_fn,
            fixture_name="c3dc",
            module_consts=module_consts,
            method_to_step=methods,
            require_query_file=False,
            default_query_file=C3DC_STATIC_DATA_FILE,
        )


register_profile(
    ExcelCaseProfile(
        app_key="C3DC",
        testcases_dir="C3DC",
        fixture="c3dc",
        input_files_prefix="InputFiles/C3DC",
        excel_actions=C3DC_EXCEL_ACTIONS,
        parse_test_function=_parse_c3dc_test_function,
        case_subdirs=C3DC_CASE_SUBDIRS,
        extra_handlers={
            "open_studies_listing": _open_studies_listing,
            "verify_studies_listing": _verify_studies_listing,
        },
    )
)
