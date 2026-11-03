"""INS — Excel testcase profile (Programs + DataSets under Testcases/INS/)."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

INS_EXCEL_ACTIONS = [
    "accept_banner",
    "click",
    "open_programs",
    "open_datasets",
    "select_filter",
    "read_statbar",
    "verify_tab",
    "verify_datasets_tab",
    "verify_static_data",
    "verify_all_tabs",
    "assert_no_failures",
]

INS_CASE_SUBDIRS = (
    "Programs/CancerType",
    "Programs/SpecialTopic",
    "DataSets",
    "static",
)

INS_STATIC_DATA_FILE = "INS_StaticData.xlsx"


def _open_programs(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.open_programs()


def _open_datasets(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.open_datasets()


def _verify_datasets_tab(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.verify_datasets_tab()


def _click_step(app: "BaseApp", page: str, params: str, _flt, _excel) -> None:
    key = f"{page}/{params}".strip("/") if page and params else (params or page).strip()
    if not key:
        raise ValueError("click step needs ObjectRepository key in Page/Params")
    app.click(key)


def _verify_static_data(app: "BaseApp", _page, params, _flt, _excel) -> None:
    sheet = (params or "").strip()
    if not sheet:
        raise ValueError("verify_static_data step needs sheet name in Params")
    app.verify_static_data(sheet)


def _ins_method_to_step() -> dict:
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
        "open_programs": lambda _a: ("open_programs", "", "", ""),
        "open_datasets": lambda _a: ("open_datasets", "", "", ""),
        "read_statbar": lambda _a: ("read_statbar", "", "", ""),
        "verify_datasets_tab": lambda _a: ("verify_datasets_tab", "", "", ""),
        "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
        "select_filter": _filter,
        "verify_tab": _tab,
        "click": _click,
        "verify_static_data": _static,
    }


def _parse_ins_test_function(test_fn: ast.FunctionDef, module_consts: dict) -> tuple[str, List[StepRow]]:
    methods = _ins_method_to_step()
    try:
        return parse_adapter_calls(
            test_fn,
            fixture_name="ins",
            module_consts=module_consts,
            method_to_step=methods,
        )
    except ValueError as err:
        if "load_query_file" not in str(err):
            raise
        query_file, steps = parse_adapter_calls(
            test_fn,
            fixture_name="ins",
            module_consts=module_consts,
            method_to_step=methods,
            require_query_file=False,
            default_query_file=INS_STATIC_DATA_FILE,
        )
        return query_file, steps


register_profile(
    ExcelCaseProfile(
        app_key="INS",
        testcases_dir="INS",
        fixture="ins",
        input_files_prefix="InputFiles/INS",
        excel_actions=INS_EXCEL_ACTIONS,
        parse_test_function=_parse_ins_test_function,
        case_subdirs=INS_CASE_SUBDIRS,
        extra_handlers={
            "open_programs": _open_programs,
            "open_datasets": _open_datasets,
            "verify_datasets_tab": _verify_datasets_tab,
            "click": _click_step,
            "verify_static_data": _verify_static_data,
        },
    )
)
