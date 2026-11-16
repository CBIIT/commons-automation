"""C3DC — Excel testcase profile (Explore Participants + static pages)."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import int_arg, parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

C3DC_EXCEL_ACTIONS = [
    "accept_banner",
    "open_explore",
    "open_studies_listing",
    "open_study_details",
    "begin_study_details_report",
    "verify_study_details",
    "create_cohort_from_all_participants",
    "verify_cohort_created",
    "open_cohorts", "close_cohorts", "duplicate_selected_cohort", "verify_duplicate_cohort_created",
    "duplicate_cohort_repeatedly", "verify_duplicate_cohort_limit",
    "update_cohort_details", "save_cohort_changes", "verify_cohort_details_saved",
    "verify_cohort_removal_confirmation",
    "download_cohort_manifest", "verify_cohort_manifest",
    "download_cohort_metadata", "verify_cohort_metadata",
    "verify_cohort_tooltip",
    "verify_selected_participants_option", "select_participant_page", "create_cohort_from_selected_participants",
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
    "study_details",
    "cohorts",
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
        "open_study_details": lambda a: ("open_study_details", "StudyDetails", str_arg(a[0]), ""),
        "begin_study_details_report": lambda a: ("begin_study_details_report", "StudyDetails", str_arg(a[0]) if a else "", ""),
        "verify_study_details": lambda a: ("verify_study_details", "StudyDetails", str_arg(a[0]), ""),
        "create_cohort_from_all_participants": lambda _a: ("create_cohort_from_all_participants", "Cohort", "", ""),
        "verify_cohort_created": lambda _a: ("verify_cohort_created", "Cohort", "", ""),
        "open_cohorts": lambda _a: ("open_cohorts", "Cohort", "", ""),
        "close_cohorts": lambda _a: ("close_cohorts", "Cohort", "", ""),
        "duplicate_selected_cohort": lambda _a: ("duplicate_selected_cohort", "Cohort", "", ""),
        "verify_duplicate_cohort_created": lambda _a: ("verify_duplicate_cohort_created", "Cohort", "", ""),
        "duplicate_cohort_repeatedly": lambda a: ("duplicate_cohort_repeatedly", "Cohort", str(int_arg(a[0])), ""),
        "verify_duplicate_cohort_limit": lambda _a: ("verify_duplicate_cohort_limit", "Cohort", "", ""),
        "update_cohort_details": lambda a: ("update_cohort_details", "Cohort", str_arg(a[0]), str_arg(a[1])),
        "save_cohort_changes": lambda _a: ("save_cohort_changes", "Cohort", "", ""),
        "verify_cohort_details_saved": lambda _a: ("verify_cohort_details_saved", "Cohort", "", ""),
        "verify_cohort_removal_confirmation": lambda a: ("verify_cohort_removal_confirmation", "Cohort", str_arg(a[0]), str_arg(a[1])),
        "download_cohort_manifest": lambda a: ("download_cohort_manifest", "Cohort", str_arg(a[0]) if a else "", ""),
        "verify_cohort_manifest": lambda _a: ("verify_cohort_manifest", "Cohort", "", ""),
        "download_cohort_metadata": lambda a: ("download_cohort_metadata", "Cohort", str_arg(a[0]) if a else "", ""),
        "verify_cohort_metadata": lambda _a: ("verify_cohort_metadata", "Cohort", "", ""),
        "verify_cohort_tooltip": lambda a: ("verify_cohort_tooltip", "Cohort", str_arg(a[0]), str_arg(a[1])),
        "verify_selected_participants_option": lambda a: ("verify_selected_participants_option", "Cohort", str_arg(a[0]), ""),
        "select_participant_page": lambda a: ("select_participant_page", "Cohort", str(int_arg(a[0])), ""),
        "create_cohort_from_selected_participants": lambda _a: ("create_cohort_from_selected_participants", "Cohort", "", ""),
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
            "open_study_details": lambda app, _p, accession, _f, _e: app.open_study_details(accession),
            "begin_study_details_report": lambda app, _p, name, _f, _e: app.begin_study_details_report(name) if name else app.begin_study_details_report(),
            "verify_study_details": lambda app, _p, accession, _f, _e: app.verify_study_details(accession),
            "create_cohort_from_all_participants": lambda app, _p, _a, _f, _e: app.create_cohort_from_all_participants(),
            "verify_cohort_created": lambda app, _p, _a, _f, _e: app.verify_cohort_created(),
            "open_cohorts": lambda app, _p, _a, _f, _e: app.open_cohorts(),
            "close_cohorts": lambda app, _p, _a, _f, _e: app.close_cohorts(),
            "duplicate_selected_cohort": lambda app, _p, _a, _f, _e: app.duplicate_selected_cohort(),
            "verify_duplicate_cohort_created": lambda app, _p, _a, _f, _e: app.verify_duplicate_cohort_created(),
            "duplicate_cohort_repeatedly": lambda app, _p, count, _f, _e: app.duplicate_cohort_repeatedly(int(count)),
            "verify_duplicate_cohort_limit": lambda app, _p, _a, _f, _e: app.verify_duplicate_cohort_limit(),
            "update_cohort_details": lambda app, _p, name, description, _e: app.update_cohort_details(name, description),
            "save_cohort_changes": lambda app, _p, _a, _f, _e: app.save_cohort_changes(),
            "verify_cohort_details_saved": lambda app, _p, _a, _f, _e: app.verify_cohort_details_saved(),
            "verify_cohort_removal_confirmation": lambda app, _p, target, message, _e: app.verify_cohort_removal_confirmation(target, message),
            "download_cohort_manifest": lambda app, _p, name, _f, excel: app.download_cohort_manifest(name or excel),
            "verify_cohort_manifest": lambda app, _p, _a, _f, _e: app.verify_cohort_manifest(),
            "download_cohort_metadata": lambda app, _p, name, _f, excel: app.download_cohort_metadata(name or excel),
            "verify_cohort_metadata": lambda app, _p, _a, _f, _e: app.verify_cohort_metadata(),
            "verify_cohort_tooltip": lambda app, _p, control, expected, _e: app.verify_cohort_tooltip(control, expected),
            "verify_selected_participants_option": lambda app, _p, state, _f, _e: app.verify_selected_participants_option(state),
            "select_participant_page": lambda app, _p, number, _f, _e: app.select_participant_page(int(number)),
            "create_cohort_from_selected_participants": lambda app, _p, _a, _f, _e: app.create_cohort_from_selected_participants(),
        },
    )
)
