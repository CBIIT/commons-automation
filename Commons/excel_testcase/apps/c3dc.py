"""C3DC — Excel testcase profile (Explore Participants + static pages)."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, List

from Commons.excel_testcase._step_parse import int_arg, parse_adapter_calls, str_arg
from Commons.excel_testcase.file_cart_steps import c3dc_cart_handlers
from Commons.excel_testcase.profile import ExcelCaseProfile, StepRow
from Commons.excel_testcase.registry import register_profile

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

C3DC_EXCEL_ACTIONS = [
    *c3dc_cart_handlers(),
    "download_result_tab", "verify_result_tab_download",
    "verify_explore_help_content",
    "open_release_notes", "verify_release_notes_content", "open_user_guide", "verify_user_guide_content",
    "open_home_page", "verify_home_page_content", "open_about_page", "verify_about_page_content",
    "verify_uploaded_cohort_participants",
    "type_formatted_participant_ids",
    "verify_unmatched_participants",
    "remember_participant_upload_baseline", "type_replacement_participant_ids", "close_participant_upload", "verify_participant_upload_empty", "remove_participant_upload", "verify_participant_upload_cleared",
    "verify_participant_upload_limit",
    "prepare_participant_upload_update", "use_replacement_participant_upload", "verify_participant_upload_draft",
    "prepare_participant_upload", "open_participant_upload", "type_participant_ids",
    "create_participant_upload_file", "attach_participant_file", "clear_participant_upload", "cancel_participant_upload",
    "submit_participant_upload", "verify_upload_preview", "verify_uploaded_participants",
    "accept_banner",
    "open_explore",
    "open_explore_files",
    "sort_result_tab",
    "verify_result_tab_sorting",
    "open_studies_listing",
    "open_study_details",
    "begin_study_details_report",
    "verify_study_details",
    "create_cohort_from_all_participants",
    "verify_cohort_created",
    "open_cohorts", "close_cohorts", "duplicate_selected_cohort", "verify_duplicate_cohort_created",
    "duplicate_cohort_repeatedly", "verify_duplicate_cohort_limit",
    "update_cohort_details", "save_cohort_changes", "verify_cohort_details_saved",
    "verify_duplicate_cohort_name_rejected",
    "verify_cohort_participant_search", "remove_cohort_participant", "verify_cohort_participant_removed",
    "verify_cohort_removal_confirmation",
    "download_cohort_manifest", "verify_cohort_manifest",
    "download_cohort_metadata", "verify_cohort_metadata",
    "verify_cohort_tooltip",
    "remember_cohort_for_addition", "replace_cohort_filter",
    "add_all_participants_to_existing_cohort", "verify_participants_added_to_cohort",
    "add_selected_participants_to_existing_cohort", "select_next_participant_page_only",
    "open_cohort_analyzer", "add_example_cohorts", "verify_example_cohorts_created",
    "remember_analyzer_cohorts",
    "verify_analyzer_empty_state",
    "verify_analyzer_existing_cohorts",
    "verify_analyzer_selection",
    "verify_analyzer_selection_limit",
    "verify_analyzer_sorting",
    "verify_analyzer_removal",
    "verify_analyzer_comparison",
    "verify_analyzer_regions",
    "create_analyzer_cohort_from_results",
    "verify_analyzer_table",
    "verify_analyzer_pagination",
    "verify_analyzer_table_download",
    "verify_analyzer_build_explore",
    "verify_analyzer_chart_values",
    "verify_analyzer_chart_types",
    "verify_analyzer_chart_management",
    "verify_analyzer_layout_reset",
    "verify_analyzer_expanded_views",
    "verify_analyzer_survival",
    "verify_analyzer_venn_downloads",
    "verify_analyzer_histogram_downloads",
    "verify_analyzer_survival_downloads",
    "verify_analyzer_data_downloads",
    "verify_analyzer_image_downloads",
    "verify_analyzer_tooltip",
    "verify_analyzer_readme",

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
    "result_tabs",
    "file_cart",
    "study_listing",
    "study_details",
    "cohorts",
    "cohort_analyzer",
    "upload_participants",
    "static",
)


def _open_studies_listing(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.open_studies_listing()


def _verify_studies_listing(app: "BaseApp", _p, _a, _b, _excel) -> None:
    app.verify_studies_listing()



def _open_cohort_analyzer_step(app, _p, _a, _f, excel_name):
    """Keep Analyzer evidence under this testcase, including UI-only checks."""
    output = getattr(app, 'output_dir', None)
    if isinstance(output, Path):
        app._analyzer_output = output / Path(excel_name).stem
    app.open_cohort_analyzer()


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
        "type_formatted_participant_ids": lambda a: ("type_formatted_participant_ids", "UploadParticipants", str(int_arg(a[0])) if a else "2", ""),
        "prepare_participant_upload_update": lambda a: ("prepare_participant_upload_update", "UploadParticipants", str(int_arg(a[0])) if a else "2", str(int_arg(a[1])) if len(a) > 1 else "0"),
        "use_replacement_participant_upload": lambda _a: ("use_replacement_participant_upload", "UploadParticipants", "", ""),
        "verify_participant_upload_draft": lambda a: ("verify_participant_upload_draft", "UploadParticipants", str_arg(a[0]) if a else "", ""),
        "verify_unmatched_participants": lambda a: ("verify_unmatched_participants", "UploadParticipants", str_arg(a[0]), ""),
        "verify_participant_upload_limit": lambda a: ("verify_participant_upload_limit", "UploadParticipants", str(int_arg(a[0])), ""),
        "remember_participant_upload_baseline": lambda _a: ("remember_participant_upload_baseline", "UploadParticipants", "", ""),
        "type_replacement_participant_ids": lambda _a: ("type_replacement_participant_ids", "UploadParticipants", "", ""),
        "close_participant_upload": lambda _a: ("close_participant_upload", "UploadParticipants", "", ""),
        "verify_participant_upload_empty": lambda _a: ("verify_participant_upload_empty", "UploadParticipants", "", ""),
        "remove_participant_upload": lambda _a: ("remove_participant_upload", "UploadParticipants", "", ""),
        "verify_participant_upload_cleared": lambda _a: ("verify_participant_upload_cleared", "UploadParticipants", "", ""),
        "prepare_participant_upload": lambda a: ("prepare_participant_upload", "UploadParticipants", str(int_arg(a[0])) if a else "2", str(int_arg(a[1])) if len(a) > 1 else "0"),
        "open_participant_upload": lambda _a: ("open_participant_upload", "UploadParticipants", "", ""),
        "type_participant_ids": lambda a: ("type_participant_ids", "UploadParticipants", str_arg(a[0]) if a else "", ""),
        "create_participant_upload_file": lambda a: ("create_participant_upload_file", "UploadParticipants", str_arg(a[1]) if len(a) > 1 else "participants.txt", ""),
        "attach_participant_file": lambda a: ("attach_participant_file", "UploadParticipants", str_arg(a[0]) if a else "", ""),
        "clear_participant_upload": lambda _a: ("clear_participant_upload", "UploadParticipants", "", ""),
        "cancel_participant_upload": lambda _a: ("cancel_participant_upload", "UploadParticipants", "", ""),
        "submit_participant_upload": lambda _a: ("submit_participant_upload", "UploadParticipants", "", ""),
        "verify_upload_preview": lambda _a: ("verify_upload_preview", "UploadParticipants", "", ""),
        "verify_uploaded_participants": lambda _a: ("verify_uploaded_participants", "UploadParticipants", "", ""),
        "accept_banner": lambda _a: ("accept_banner", "", "", ""),
        "open_explore": lambda _a: ("open_explore", "", "", ""),
        "open_explore_files": lambda _a: ("open_explore_files", "", "", ""),
        "sort_result_tab": lambda a: ("sort_result_tab", str_arg(a[0]), str_arg(a[1]), ""),
        "open_studies_listing": lambda _a: ("open_studies_listing", "", "", ""),
        "verify_studies_listing": lambda _a: ("verify_studies_listing", "", "", ""),
        "open_study_details": lambda a: ("open_study_details", "StudyDetails", str_arg(a[0]), ""),
        "begin_study_details_report": lambda a: ("begin_study_details_report", "StudyDetails", str_arg(a[0]) if a else "", ""),
        "verify_study_details": lambda a: ("verify_study_details", "StudyDetails", str_arg(a[0]), ""),
        "create_cohort_from_all_participants": lambda _a: ("create_cohort_from_all_participants", "Cohort", "", ""),
        "verify_uploaded_cohort_participants": lambda _a: ("verify_uploaded_cohort_participants", "Cohort", "", ""),
        "verify_cohort_created": lambda _a: ("verify_cohort_created", "Cohort", "", ""),
        "open_cohorts": lambda _a: ("open_cohorts", "Cohort", "", ""),
        "close_cohorts": lambda _a: ("close_cohorts", "Cohort", "", ""),
        "duplicate_selected_cohort": lambda _a: ("duplicate_selected_cohort", "Cohort", "", ""),
        "verify_duplicate_cohort_created": lambda _a: ("verify_duplicate_cohort_created", "Cohort", "", ""),
        "duplicate_cohort_repeatedly": lambda a: ("duplicate_cohort_repeatedly", "Cohort", str(int_arg(a[0])), ""),
        "verify_duplicate_cohort_limit": lambda _a: ("verify_duplicate_cohort_limit", "Cohort", "", ""),
        "update_cohort_details": lambda a: ("update_cohort_details", "Cohort", str_arg(a[0]), str_arg(a[1])),
        "verify_duplicate_cohort_name_rejected": lambda a: ("verify_duplicate_cohort_name_rejected", "Cohort", "", str_arg(a[0])),
        "verify_cohort_participant_search": lambda _a: ("verify_cohort_participant_search", "Cohort", "", ""),
        "remove_cohort_participant": lambda _a: ("remove_cohort_participant", "Cohort", "", ""),
        "verify_cohort_participant_removed": lambda _a: ("verify_cohort_participant_removed", "Cohort", "", ""),
        "save_cohort_changes": lambda _a: ("save_cohort_changes", "Cohort", "", ""),
        "verify_cohort_details_saved": lambda _a: ("verify_cohort_details_saved", "Cohort", "", ""),
        "verify_cohort_removal_confirmation": lambda a: ("verify_cohort_removal_confirmation", "Cohort", str_arg(a[0]), str_arg(a[1])),
        "download_cohort_manifest": lambda a: ("download_cohort_manifest", "Cohort", str_arg(a[0]) if a else "", ""),
        "verify_cohort_manifest": lambda _a: ("verify_cohort_manifest", "Cohort", "", ""),
        "download_cohort_metadata": lambda a: ("download_cohort_metadata", "Cohort", str_arg(a[0]) if a else "", ""),
        "verify_cohort_metadata": lambda _a: ("verify_cohort_metadata", "Cohort", "", ""),
        "verify_cohort_tooltip": lambda a: ("verify_cohort_tooltip", "Cohort", str_arg(a[0]), str_arg(a[1])),
        "remember_cohort_for_addition": lambda _a: ("remember_cohort_for_addition", "Cohort", "", ""),
        "replace_cohort_filter": lambda a: ("replace_cohort_filter", str_arg(a[0]), str_arg(a[1]), str_arg(a[2])),
        "add_all_participants_to_existing_cohort": lambda _a: ("add_all_participants_to_existing_cohort", "Cohort", "", ""),
        "add_selected_participants_to_existing_cohort": lambda _a: ("add_selected_participants_to_existing_cohort", "Cohort", "", ""),
        "select_next_participant_page_only": lambda _a: ("select_next_participant_page_only", "Cohort", "", ""),
        "verify_participants_added_to_cohort": lambda _a: ("verify_participants_added_to_cohort", "Cohort", "", ""),
        "remember_analyzer_cohorts": lambda a: ("remember_analyzer_cohorts", "CohortAnalyzer", "", str_arg(a[1]) if len(a) > 1 else ""),
        "verify_analyzer_empty_state": lambda _a: ("verify_analyzer_empty_state", "CohortAnalyzer", "", ""),
        "verify_analyzer_existing_cohorts": lambda _a: ("verify_analyzer_existing_cohorts", "CohortAnalyzer", "", ""),
        "verify_analyzer_selection": lambda _a: ("verify_analyzer_selection", "CohortAnalyzer", "", ""),
        "verify_analyzer_selection_limit": lambda _a: ("verify_analyzer_selection_limit", "CohortAnalyzer", "", ""),
        "verify_analyzer_sorting": lambda _a: ("verify_analyzer_sorting", "CohortAnalyzer", "", ""),
        "verify_analyzer_removal": lambda a: ("verify_analyzer_removal", "CohortAnalyzer", str_arg(a[0]), str_arg(a[1])),
        "verify_analyzer_comparison": lambda a: ("verify_analyzer_comparison", "CohortAnalyzer", str_arg(a[0]), ""),
        "verify_analyzer_regions": lambda _a: ("verify_analyzer_regions", "CohortAnalyzer", "", ""),
        "create_analyzer_cohort_from_results": lambda _a: ("create_analyzer_cohort_from_results", "CohortAnalyzer", "", ""),
        "verify_analyzer_table": lambda _a: ("verify_analyzer_table", "CohortAnalyzer", "", ""),
        "verify_analyzer_pagination": lambda _a: ("verify_analyzer_pagination", "CohortAnalyzer", "", ""),
        "verify_analyzer_table_download": lambda a: ("verify_analyzer_table_download", "CohortAnalyzer", str_arg(a[0]), ""),
        "verify_analyzer_build_explore": lambda a: ("verify_analyzer_build_explore", "CohortAnalyzer", "", str_arg(a[0])),
        "verify_analyzer_chart_values": lambda _a: ("verify_analyzer_chart_values", "CohortAnalyzer", "", ""),
        "verify_analyzer_chart_types": lambda _a: ("verify_analyzer_chart_types", "CohortAnalyzer", "", ""),
        "verify_analyzer_chart_management": lambda _a: ("verify_analyzer_chart_management", "CohortAnalyzer", "", ""),
        "verify_analyzer_layout_reset": lambda _a: ("verify_analyzer_layout_reset", "CohortAnalyzer", "", ""),
        "verify_analyzer_expanded_views": lambda _a: ("verify_analyzer_expanded_views", "CohortAnalyzer", "", ""),
        "verify_analyzer_survival": lambda _a: ("verify_analyzer_survival", "CohortAnalyzer", "", ""),
        "verify_analyzer_venn_downloads": lambda _a: ("verify_analyzer_venn_downloads", "CohortAnalyzer", "", ""),
        "verify_analyzer_histogram_downloads": lambda _a: ("verify_analyzer_histogram_downloads", "CohortAnalyzer", "", ""),
        "verify_analyzer_survival_downloads": lambda _a: ("verify_analyzer_survival_downloads", "CohortAnalyzer", "", ""),
        "verify_analyzer_data_downloads": lambda _a: ("verify_analyzer_data_downloads", "CohortAnalyzer", "", ""),
        "verify_analyzer_image_downloads": lambda _a: ("verify_analyzer_image_downloads", "CohortAnalyzer", "", ""),
        "verify_analyzer_tooltip": lambda a: ("verify_analyzer_tooltip", "CohortAnalyzer", str_arg(a[0]), str_arg(a[1])),
        "verify_analyzer_readme": lambda _a: ("verify_analyzer_readme", "CohortAnalyzer", "", ""),
        "open_cohort_analyzer": lambda _a: ("open_cohort_analyzer", "CohortAnalyzer", "", ""),
        "add_example_cohorts": lambda _a: ("add_example_cohorts", "CohortAnalyzer", "", ""),
        "verify_example_cohorts_created": lambda a: ("verify_example_cohorts_created", "CohortAnalyzer", "", str_arg(a[0])),
        "verify_selected_participants_option": lambda a: ("verify_selected_participants_option", "Cohort", str_arg(a[0]), ""),
        "select_participant_page": lambda a: ("select_participant_page", "Cohort", str(int_arg(a[0])), ""),
        "create_cohort_from_selected_participants": lambda _a: ("create_cohort_from_selected_participants", "Cohort", "", ""),
        "read_statbar": lambda _a: ("read_statbar", "", "", ""),
        "assert_no_failures": lambda _a: ("assert_no_failures", "", "", ""),
        "select_filter": _filter,
        "verify_tab": _tab,
        "goto": _goto,
        "open_home_page": lambda _a: ("open_home_page", "", "", ""),
        "verify_home_page_content": lambda _a: ("verify_home_page_content", "", "", ""),
        "open_about_page": lambda _a: ("open_about_page", "", "", ""),
        "verify_about_page_content": lambda _a: ("verify_about_page_content", "", "", ""),
        "open_release_notes": lambda _a: ("open_release_notes", "", "", ""),
        "verify_release_notes_content": lambda _a: ("verify_release_notes_content", "", "", ""),
        "open_user_guide": lambda _a: ("open_user_guide", "", "", ""),
        "verify_user_guide_content": lambda _a: ("verify_user_guide_content", "", "", ""),
        "verify_explore_help_content": lambda a: ("verify_explore_help_content", "", str_arg(a[0]), ""),
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
            **c3dc_cart_handlers(),
            "download_result_tab": lambda app, tab, fmt, _f, case: app.result_tabs.download(tab, fmt, case),
            "verify_result_tab_download": lambda app, tab, fmt, _f, _e: app.result_tabs.verify_download(tab, fmt),
            "sort_result_tab": lambda app, tab, column, _f, _e: app.sort_result_tab(tab, column),
            "open_explore_files": lambda app, _p, _a, _f, _e: app.open_explore_files(),
            "open_studies_listing": _open_studies_listing,
            "verify_studies_listing": _verify_studies_listing,
            "open_study_details": lambda app, _p, accession, _f, _e: app.open_study_details(accession),
            "begin_study_details_report": lambda app, _p, name, _f, _e: app.begin_study_details_report(name) if name else app.begin_study_details_report(),
            "verify_study_details": lambda app, _p, accession, _f, _e: app.verify_study_details(accession),
            "open_home_page": lambda app, _p, _a, _f, _e: app.open_home_page(),
            "verify_home_page_content": lambda app, _p, _a, _f, _e: app.verify_home_page_content(),
            "open_about_page": lambda app, _p, _a, _f, _e: app.open_about_page(),
            "verify_about_page_content": lambda app, _p, _a, _f, _e: app.verify_about_page_content(),
            "open_release_notes": lambda app, _p, _a, _f, _e: app.open_release_notes(),
            "verify_release_notes_content": lambda app, _p, _a, _f, _e: app.verify_release_notes_content(),
            "open_user_guide": lambda app, _p, _a, _f, _e: app.open_user_guide(),
            "verify_user_guide_content": lambda app, _p, _a, _f, _e: app.verify_user_guide_content(),
            "verify_explore_help_content": lambda app, _p, sheet, _f, _e: app.verify_explore_help_content(sheet),
            "create_cohort_from_all_participants": lambda app, _p, _a, _f, _e: app.create_cohort_from_all_participants(),
            "verify_uploaded_cohort_participants": lambda app, _p, _a, _f, _e: app.verify_uploaded_cohort_participants(),
            "verify_cohort_created": lambda app, _p, _a, _f, _e: app.verify_cohort_created(),
            "open_cohorts": lambda app, _p, _a, _f, _e: app.open_cohorts(),
            "close_cohorts": lambda app, _p, _a, _f, _e: app.close_cohorts(),
            "duplicate_selected_cohort": lambda app, _p, _a, _f, _e: app.duplicate_selected_cohort(),
            "verify_duplicate_cohort_created": lambda app, _p, _a, _f, _e: app.verify_duplicate_cohort_created(),
            "duplicate_cohort_repeatedly": lambda app, _p, count, _f, _e: app.duplicate_cohort_repeatedly(int(count)),
            "verify_duplicate_cohort_limit": lambda app, _p, _a, _f, _e: app.verify_duplicate_cohort_limit(),
            "update_cohort_details": lambda app, _p, name, description, _e: app.update_cohort_details(name, description),
            "verify_duplicate_cohort_name_rejected": lambda app, _p, _a, message, _e: app.verify_duplicate_cohort_name_rejected(message),
            "verify_cohort_participant_search": lambda app, _p, _a, _f, _e: app.verify_cohort_participant_search(),
            "remove_cohort_participant": lambda app, _p, _a, _f, _e: app.remove_cohort_participant(),
            "verify_cohort_participant_removed": lambda app, _p, _a, _f, _e: app.verify_cohort_participant_removed(),
            "save_cohort_changes": lambda app, _p, _a, _f, _e: app.save_cohort_changes(),
            "verify_cohort_details_saved": lambda app, _p, _a, _f, _e: app.verify_cohort_details_saved(),
            "verify_cohort_removal_confirmation": lambda app, _p, target, message, _e: app.verify_cohort_removal_confirmation(target, message),
            "download_cohort_manifest": lambda app, _p, name, _f, excel: app.download_cohort_manifest(name or excel),
            "verify_cohort_manifest": lambda app, _p, _a, _f, _e: app.verify_cohort_manifest(),
            "download_cohort_metadata": lambda app, _p, name, _f, excel: app.download_cohort_metadata(name or excel),
            "verify_cohort_metadata": lambda app, _p, _a, _f, _e: app.verify_cohort_metadata(),
            "verify_cohort_tooltip": lambda app, _p, control, expected, _e: app.verify_cohort_tooltip(control, expected),
            "remember_cohort_for_addition": lambda app, _p, _a, _f, _e: app.remember_cohort_for_addition(),
            "replace_cohort_filter": lambda app, group, previous, replacement, _e: app.replace_cohort_filter(group, previous, replacement),
            "add_all_participants_to_existing_cohort": lambda app, _p, _a, _f, _e: app.add_all_participants_to_existing_cohort(),
            "add_selected_participants_to_existing_cohort": lambda app, _p, _a, _f, _e: app.add_selected_participants_to_existing_cohort(),
            "select_next_participant_page_only": lambda app, _p, _a, _f, _e: app.select_next_participant_page_only(),
            "verify_participants_added_to_cohort": lambda app, _p, _a, _f, excel: app.verify_participants_added_to_cohort(excel),
            "type_formatted_participant_ids": lambda app, _p, repetitions, _f, _e: app.type_formatted_participant_ids(int(repetitions or 2)),
            "prepare_participant_upload_update": lambda app, _p, count, unmatched, _e: app.prepare_participant_upload_update(int(count or 2), int(unmatched or 0)),
            "use_replacement_participant_upload": lambda app, _p, _a, _f, _e: app.use_replacement_participant_upload(),
            "verify_participant_upload_draft": lambda app, _p, ids, _f, _e: app.verify_participant_upload_draft(ids or None),
            "verify_unmatched_participants": lambda app, _p, count, _f, excel: app.verify_unmatched_participants(int(count or 3), excel),
            "verify_participant_upload_limit": lambda app, _p, limit, _f, excel: app.verify_participant_upload_limit(int(limit), excel),
            "remember_participant_upload_baseline": lambda app, _p, _a, _f, _e: app.remember_participant_upload_baseline(),
            "type_replacement_participant_ids": lambda app, _p, _a, _f, _e: app.type_replacement_participant_ids(),
            "close_participant_upload": lambda app, _p, _a, _f, _e: app.close_participant_upload(),
            "verify_participant_upload_empty": lambda app, _p, _a, _f, _e: app.verify_participant_upload_empty(),
            "remove_participant_upload": lambda app, _p, _a, _f, _e: app.remove_participant_upload(),
            "verify_participant_upload_cleared": lambda app, _p, _a, _f, _e: app.verify_participant_upload_cleared(),
            "prepare_participant_upload": lambda app, _p, count, unmatched, _e: app.prepare_participant_upload(int(count or 2), int(unmatched or 0)),
            "open_participant_upload": lambda app, _p, _a, _f, _e: app.open_participant_upload(),
            "type_participant_ids": lambda app, _p, ids, _f, _e: app.type_participant_ids(ids or None),
            "create_participant_upload_file": lambda app, _p, filename, _f, excel: app.create_participant_upload_file(excel, filename or "participants.txt"),
            "attach_participant_file": lambda app, _p, path, _f, _e: app.attach_participant_file(path or None),
            "clear_participant_upload": lambda app, _p, _a, _f, _e: app.clear_participant_upload(),
            "cancel_participant_upload": lambda app, _p, _a, _f, _e: app.cancel_participant_upload(),
            "submit_participant_upload": lambda app, _p, _a, _f, _e: app.submit_participant_upload(),
            "verify_upload_preview": lambda app, _p, _a, _f, _e: app.verify_upload_preview(),
            "verify_uploaded_participants": lambda app, _p, _a, _f, excel: app.verify_uploaded_participants(excel),
            "remember_analyzer_cohorts": lambda app, _p, _a, metadata, excel: app.remember_analyzer_cohorts(excel, metadata),
            "verify_analyzer_empty_state": lambda app, _p, _a, _f, _e: app.verify_analyzer_empty_state(),
            "verify_analyzer_existing_cohorts": lambda app, _p, _a, _f, _e: app.verify_analyzer_existing_cohorts(),
            "verify_analyzer_selection": lambda app, _p, _a, _f, _e: app.verify_analyzer_selection(),
            "verify_analyzer_selection_limit": lambda app, _p, _a, _f, _e: app.verify_analyzer_selection_limit(),
            "verify_analyzer_sorting": lambda app, _p, _a, _f, _e: app.verify_analyzer_sorting(),
            "verify_analyzer_removal": lambda app, _p, value, expected, _e: app.verify_analyzer_removal(value, expected),
            "verify_analyzer_comparison": lambda app, _p, value, _f, _e: app.verify_analyzer_comparison(value),
            "verify_analyzer_regions": lambda app, _p, _a, _f, _e: app.verify_analyzer_regions(),
            "create_analyzer_cohort_from_results": lambda app, _p, _a, _f, _e: app.create_analyzer_cohort_from_results(),
            "verify_analyzer_table": lambda app, _p, _a, _f, _e: app.verify_analyzer_table(),
            "verify_analyzer_pagination": lambda app, _p, _a, _f, _e: app.verify_analyzer_pagination(),
            "verify_analyzer_table_download": lambda app, _p, value, _f, _e: app.verify_analyzer_table_download(value),
            "verify_analyzer_build_explore": lambda app, _p, _a, message, _e: app.verify_analyzer_build_explore(message),
            "verify_analyzer_chart_values": lambda app, _p, _a, _f, _e: app.verify_analyzer_chart_values(),
            "verify_analyzer_chart_types": lambda app, _p, _a, _f, _e: app.verify_analyzer_chart_types(),
            "verify_analyzer_chart_management": lambda app, _p, _a, _f, _e: app.verify_analyzer_chart_management(),
            "verify_analyzer_layout_reset": lambda app, _p, _a, _f, _e: app.verify_analyzer_layout_reset(),
            "verify_analyzer_expanded_views": lambda app, _p, _a, _f, _e: app.verify_analyzer_expanded_views(),
            "verify_analyzer_survival": lambda app, _p, _a, _f, _e: app.verify_analyzer_survival(),
            "verify_analyzer_venn_downloads": lambda app, _p, _a, _f, _e: app.verify_analyzer_venn_downloads(),
            "verify_analyzer_histogram_downloads": lambda app, _p, _a, _f, _e: app.verify_analyzer_histogram_downloads(),
            "verify_analyzer_survival_downloads": lambda app, _p, _a, _f, _e: app.verify_analyzer_survival_downloads(),
            "verify_analyzer_data_downloads": lambda app, _p, _a, _f, _e: app.verify_analyzer_data_downloads(),
            "verify_analyzer_image_downloads": lambda app, _p, _a, _f, _e: app.verify_analyzer_image_downloads(),
            "verify_analyzer_tooltip": lambda app, _p, value, expected, _e: app.verify_analyzer_tooltip(value, expected),
            "verify_analyzer_readme": lambda app, _p, _a, _f, _e: app.verify_analyzer_readme(),
            "open_cohort_analyzer": _open_cohort_analyzer_step,
            "add_example_cohorts": lambda app, _p, _a, _f, _e: app.add_example_cohorts(),
            "verify_example_cohorts_created": lambda app, _p, _a, names, _e: app.verify_example_cohorts_created(names),
            "verify_selected_participants_option": lambda app, _p, state, _f, _e: app.verify_selected_participants_option(state),
            "select_participant_page": lambda app, _p, number, _f, _e: app.select_participant_page(int(number)),
            "create_cohort_from_selected_participants": lambda app, _p, _a, _f, _e: app.create_cohort_from_selected_participants(),
        },
    )
)
