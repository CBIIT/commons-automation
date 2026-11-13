"""PSDC Excel steps use the same shared handlers as CTDC."""
from Commons.excel_testcase._step_parse import parse_adapter_calls, str_arg
from Commons.excel_testcase.profile import ExcelCaseProfile
from Commons.excel_testcase.registry import register_profile


def _parse_test_function(test_fn, module_consts):
    """Keep Python-to-Excel conversion available, as it is for CTDC."""
    methods = {
        name: (lambda _args, action=name: (action, "", "", ""))
        for name in ("accept_banner", "open_explore", "read_statbar",
                     "verify_all_tabs", "assert_no_failures")
    }
    for name in ("select_study", "open_study", "verify_tab", "click", "verify_static_data"):
        methods[name] = lambda args, action=name: (action, "", str_arg(args[0]), "")
    methods["select_filter"] = lambda args: (
        "select_filter", str_arg(args[0]), "", str_arg(args[1]),
    )
    return parse_adapter_calls(
        test_fn, fixture_name="psdc", module_consts=module_consts,
        method_to_step=methods, require_query_file=False,
        default_query_file="TC01_PSDC_StaticData.xlsx",
    )


def _open_study(app, page, params, flt, _excel):
    study = params or flt or page
    if not study:
        raise ValueError("open_study step needs a study acronym in Params")
    app.open_study(study)


register_profile(
    ExcelCaseProfile(
        app_key="PSDC",
        testcases_dir="PSDC",
        fixture="psdc",
        input_files_prefix="InputFiles/PSDC",
        parse_test_function=_parse_test_function,
        excel_actions=[
            "accept_banner", "click", "open_explore", "select_study", "select_filter",
            "read_statbar", "verify_tab", "verify_all_tabs", "verify_static_data",
            "open_study", "assert_no_failures",
        ],
        case_subdirs=("studies", "static"),
        extra_handlers={"open_study": _open_study},
    )
)
