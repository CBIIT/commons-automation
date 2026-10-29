"""
Execute a test case from an Excel file (Steps sheet).

Layout:
  Row 1: Input Excel | Action | Page | Params | Filter
  Row 2: query workbook path (InputFiles/GC/TC….xlsx) — Memgraph Cypher lives in that file
  Row 3+: leave Input Excel blank; fill Action and columns as needed

Pagination/row limits: Config/tab_setting.yaml (not this workbook).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import openpyxl

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

_COL_INPUT = 0
_COL_ACTION = 1
_COL_PAGE = 2
_COL_PARAMS = 3
_COL_FILTER = 4

GC_TAB_FROM_PARAMS = {
    "ParticipantsTab": "Participants",
    "SamplesTab": "Samples",
    "FilesTab": "Files",
}


def _norm_action(action: str) -> str:
    return action.strip().lower().replace(" ", "_").replace("-", "_")


def _repo_key(page: str, params: str) -> str:
    page = (page or "").strip().strip("/")
    obj = (params or "").strip().strip("/")
    if page and obj.startswith(page + "/"):
        obj = obj[len(page) + 1 :]
    if page and obj:
        return f"{page}/{obj}"
    return page or obj


def _click(app: "BaseApp", page: str, params: str, *, js: bool = False) -> None:
    key = _repo_key(page, params)
    xp = app.repo.xpath(key)
    if js:
        app.ui.js_click(xp, repo_key=key)
    else:
        app.ui.click(xp, repo_key=key)
    app.ui.wait_idle()


def _select_filter_from_step(app: "BaseApp", page: str, params: str, flt: str) -> None:
    group = (page or params or "").strip()
    value = (flt or "").strip()
    if "=" in value and not group:
        group, value = value.split("=", 1)
        group, value = group.strip(), value.strip()
    if not group or not value:
        raise ValueError(
            f"select_filter step needs filter group (Page) and value (Filter). "
            f"Got page={page!r} params={params!r} filter={flt!r}"
        )
    app.select_filter(group, value)


def _input_excel_from_config(cfg: tuple) -> str:
    if not cfg:
        return ""
    if len(cfg) > _COL_INPUT and cfg[_COL_INPUT]:
        return str(cfg[_COL_INPUT]).strip()
    # Legacy layout: Input Excel was column D (index 2) with # / Program prefix columns
    if len(cfg) > 2 and cfg[2]:
        return str(cfg[2]).strip()
    return ""


def run_testcase_excel(app: "BaseApp", excel_path: Path) -> None:
    """Run one study-folder *.xlsx test case against an opened app fixture."""
    if not excel_path.is_file():
        raise FileNotFoundError(excel_path)

    wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)
    if "Steps" not in wb.sheetnames:
        wb.close()
        raise KeyError(f"{excel_path.name} must contain a 'Steps' sheet")
    ws = wb["Steps"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 2:
        raise ValueError(f"{excel_path.name}: Steps sheet is empty")

    input_excel = _input_excel_from_config(rows[1])
    if input_excel:
        app.load_query_file(Path(input_excel.replace("\\", "/")).name)

    for row in rows[2:]:
        if not row or len(row) <= _COL_ACTION or not row[_COL_ACTION]:
            continue
        action = _norm_action(str(row[_COL_ACTION]))
        page = str(row[_COL_PAGE]).strip() if len(row) > _COL_PAGE and row[_COL_PAGE] else ""
        params = str(row[_COL_PARAMS]).strip() if len(row) > _COL_PARAMS and row[_COL_PARAMS] else ""
        flt = str(row[_COL_FILTER]).strip() if len(row) > _COL_FILTER and row[_COL_FILTER] else ""

        if action in ("dismiss_popup", "accept_banner"):
            app.accept_banner()
        elif action == "open_data":
            app.open_data()
        elif action == "open_explore":
            app.open_explore()
        elif action in ("select_filter", "select_filter_value"):
            _select_filter_from_step(app, page, params, flt)
        elif action in ("read_stat_bar", "read_statbar"):
            app.read_statbar()
        elif action == "verify_tab":
            tab = params or page
            if not tab:
                raise ValueError("verify_tab step needs tab name in Params")
            app.verify_tab(tab)
        elif action == "verify_all_tabs":
            tabs = getattr(app, "STANDARD_VERIFY_TABS", None)
            if tabs:
                for tab in tabs:
                    app.verify_tab(tab)
            else:
                for tab in app.TABS:
                    app.verify_tab(tab)
        elif action in ("multi_function", "verify_tab_memgraph"):
            tab = GC_TAB_FROM_PARAMS.get(params, params.replace("Tab", "") if params else "")
            if tab in app.TABS or tab in (getattr(app, "TABS", {}) or {}):
                app.verify_tab(tab)
            elif params:
                app.verify_tab(params)
            else:
                raise ValueError(f"multi_function step needs tab key in Params, got {params!r}")
        elif action in ("assert_no_failures", "assert_results"):
            app.assert_no_failures()
        elif action == "load_query_file":
            if not params:
                raise ValueError("load_query_file step needs workbook name in Params")
            app.load_query_file(Path(params.replace("\\", "/")).name)
        elif action == "click_and_wait":
            _click(app, page, params, js=False)
        elif action in ("js_click_and_wait", "js_click"):
            _click(app, page, params, js=True)
        else:
            raise ValueError(
                f"Unknown step action {action!r} in {excel_path.name}. "
                "Use accept_banner, open_data, select_filter, read_statbar, verify_tab, assert_no_failures, …"
            )
