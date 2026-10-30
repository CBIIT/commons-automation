"""Step handlers shared across apps (select_filter, verify_tab, …)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp

Handler = Callable[["BaseApp", str, str, str, str], None]  # app, page, params, filter, excel_name


def norm_action(action: str) -> str:
    return action.strip().lower().replace(" ", "_").replace("-", "_")


def repo_key(page: str, params: str) -> str:
    page = (page or "").strip().strip("/")
    obj = (params or "").strip().strip("/")
    if page and obj.startswith(page + "/"):
        obj = obj[len(page) + 1 :]
    if page and obj:
        return f"{page}/{obj}"
    return page or obj


def click(app: "BaseApp", page: str, params: str, *, js: bool = False) -> None:
    key = repo_key(page, params)
    xp = app.repo.xpath(key)
    if js:
        app.ui.js_click(xp, repo_key=key)
    else:
        app.ui.click(xp, repo_key=key)
    app.ui.wait_idle()


def select_filter_from_step(app: "BaseApp", page: str, params: str, flt: str, _excel: str = "") -> None:
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


def common_handlers() -> Dict[str, Handler]:
    def accept_banner(app, _p, _a, _b, _excel):
        app.accept_banner()

    def open_data(app, _p, _a, _b, _excel):
        app.open_data()

    def open_explore(app, _p, _a, _b, _excel):
        app.open_explore()

    def open_cases(app, _p, _a, _b, _excel):
        app.open_cases()

    def select_study(app, page, params, flt, _excel):
        study = params or flt or page
        if not study:
            raise ValueError("select_study step needs study id in Params")
        if hasattr(app, "select_study"):
            app.select_study(study)
        else:
            app.select_filter("Studies/Study", study)

    def read_statbar(app, _p, _a, _b, _excel):
        app.read_statbar()

    def verify_tab(app, page, params, _flt, _excel):
        tab = params or page
        if not tab:
            raise ValueError("verify_tab step needs tab name in Params")
        app.verify_tab(tab)

    def verify_all_tabs(app, _p, _a, _b, _excel):
        tabs = getattr(app, "STANDARD_VERIFY_TABS", None)
        if tabs:
            for tab in tabs:
                app.verify_tab(tab)
        else:
            for tab in app.TABS:
                app.verify_tab(tab)

    def assert_no_failures(app, _p, _a, _b, _excel):
        app.assert_no_failures()

    def load_query_file(app, _page, params, _flt, _excel):
        from pathlib import Path

        if not params:
            raise ValueError("load_query_file step needs workbook name in Params")
        app.load_query_file(Path(params.replace("\\", "/")).name)

    def click_and_wait(app, page, params, _flt, _excel):
        click(app, page, params, js=False)

    def js_click(app, page, params, _flt, _excel):
        click(app, page, params, js=True)

    def set_age_range(app, _page, params, _flt, _excel):
        text = (params or "").strip()
        if "," not in text:
            raise ValueError("set_age_range step needs min,max in Params (e.g. 10,30)")
        lo, hi = text.split(",", 1)
        app.set_age_range(int(lo.strip()), int(hi.strip()))

    return {
        "dismiss_popup": accept_banner,
        "accept_banner": accept_banner,
        "open_data": open_data,
        "open_explore": open_explore,
        "open_cases": open_cases,
        "select_study": select_study,
        "select_filter": lambda app, p, a, f, e: select_filter_from_step(app, p, a, f, e),
        "select_filter_value": lambda app, p, a, f, e: select_filter_from_step(app, p, a, f, e),
        "read_stat_bar": read_statbar,
        "read_statbar": read_statbar,
        "verify_tab": verify_tab,
        "verify_all_tabs": verify_all_tabs,
        "assert_no_failures": assert_no_failures,
        "assert_results": assert_no_failures,
        "load_query_file": load_query_file,
        "click_and_wait": click_and_wait,
        "js_click_and_wait": js_click,
        "js_click": js_click,
        "set_age_range": set_age_range,
    }
