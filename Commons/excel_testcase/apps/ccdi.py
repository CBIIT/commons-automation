"""CCDI Hub Excel profile: separate static and functional testcase folders."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase._common_steps import repo_key
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

CCDI_EXCEL_ACTIONS = [
    "accept_banner",
    "click",
    "verify_static_data",
    "verify_home_page",
    "verify_home_controls",
    "verify_about_page_data",
    "verify_link_navigation",
    "verify_carousel_link",
    "verify_home_control_action",
    "write_home_control_results",
    "assert_no_failures",
]

CCDI_STATIC_DATA_FILE = "CCDI_StaticData.xlsx"

CCDI_CASE_SUBDIRS = ("static", "functional")


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

    def _control(action, args):
        key = str_arg(args[0])
        page, obj = key.rsplit("/", 1)
        return (action, page, obj, str_arg(args[1]) if len(args) > 1 else "")

    return {
        "accept_banner": lambda _a: ("accept_banner", "", "", ""),
        "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
        "click": _click,
        "verify_static_data": _static,
        "verify_home_page": lambda _a: ("verify_home_page", "", "", ""),
        "verify_home_controls": lambda _a: ("verify_home_controls", "", "", ""),
        "verify_about_page_data": lambda _a: ("verify_about_page_data", "", "", ""),
        "verify_link_navigation": lambda a: _control("verify_link_navigation", a),
        "verify_carousel_link": lambda a: _control("verify_carousel_link", a),
        "verify_home_control_action": lambda a: _control("verify_home_control_action", a),
        "write_home_control_results": lambda _a: ("write_home_control_results", "", "", ""),
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
        extra_handlers={
            "click": _click_step,
            "verify_home_page": lambda app, _p, _a, _f, _e: app.verify_home_page(),
            "verify_home_controls": lambda app, _p, _a, _f, _e: app.verify_home_controls(),
            "verify_about_page_data": lambda app, _p, _a, _f, _e: app.verify_about_page_data(),
            "verify_link_navigation": lambda app, p, a, f, _e: app.verify_link_navigation(repo_key(p, a), f),
            "verify_carousel_link": lambda app, p, a, f, _e: app.verify_carousel_link(repo_key(p, a), f),
            "verify_home_control_action": lambda app, p, a, f, _e: app.verify_home_control_action(repo_key(p, a), f),
            "write_home_control_results": lambda app, _p, _a, _f, _e: app.write_home_control_results(),
        },
    )
)
