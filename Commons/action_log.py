"""
Katalon-style console tracing (System.out.println / clickTab / table row dumps).

Enable with:
  pytest --trace-actions ...
  export COMMONS_VERBOSE=1
  COMMONS_VERBOSE=1 in gitignored .env

Human-readable UI steps (always shown during tests unless disabled):
  COMMONS_UI_ACTIONS=1   default on; set 0 to hide "[UI] …" lines

Memgraph Cypher (always shown when a query runs unless disabled):
  COMMONS_DB_QUERIES=1   default on; set 0 to hide "[DB] …" query text

Browser open/close and navigation (always shown during tests unless disabled):
  COMMONS_BROWSER_LOG=1  default on; set 0 to hide "[Browser] …" lines
"""
from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from typing import Any, Iterable, Iterator, List, Optional, Sequence

# ---------------------------------------------------------------------------
# Pytest live console (table compare / stat bar during capture)
# ---------------------------------------------------------------------------

_pytest_config: Any = None


def set_pytest_config(config: Any) -> None:
    """Registered from conftest pytest_configure (get_config() alone has no capturemanager)."""
    global _pytest_config
    _pytest_config = config


def _capture_manager() -> Any:
    if _pytest_config is None:
        return None
    try:
        return _pytest_config.pluginmanager.getplugin("capturemanager")
    except Exception:
        return None


def table_live_print(msg: str) -> None:
    """Katalon-style table line (one print; use with pytest_table_output_live during reads)."""
    print(msg, flush=True)


@contextmanager
def pytest_table_output_live() -> Iterator[None]:
    """
    While reading a table, let stdout/stderr go straight to the terminal (pytest -s effect).

    Only active under pytest when global capture is on; no-op elsewhere.
    """
    capman = _capture_manager()
    suspended = False
    if capman is not None and capman.is_globally_capturing():
        capman.suspend_global_capture(in_=False)
        suspended = True
    try:
        yield
    finally:
        if suspended and capman is not None:
            capman.resume_global_capture()


# ---------------------------------------------------------------------------
# Verbose trace (COMMONS_VERBOSE — Katalon System.out parity)
# ---------------------------------------------------------------------------

_enabled: Optional[bool] = None


def enabled() -> bool:
    global _enabled
    if _enabled is None:
        _enabled = os.environ.get("COMMONS_VERBOSE", "").strip().lower() in ("1", "true", "yes", "on")
    return _enabled


def set_enabled(on: bool) -> None:
    global _enabled
    _enabled = on


def say(msg: str) -> None:
    if enabled():
        print(msg, flush=True)


# ---------------------------------------------------------------------------
# UI step confirmations ([UI] — COMMONS_UI_ACTIONS)
# ---------------------------------------------------------------------------

_ui_actions: Optional[bool] = None


def ui_actions_enabled() -> bool:
    """Print plain-language confirmation for each UI step (on by default)."""
    global _ui_actions
    if _ui_actions is None:
        raw = os.environ.get("COMMONS_UI_ACTIONS", "1").strip().lower()
        _ui_actions = raw not in ("0", "false", "no", "off")
    return _ui_actions


def set_ui_actions(on: bool) -> None:
    global _ui_actions
    _ui_actions = on


def ui_action(msg: str) -> None:
    """Console line for a completed UI step, e.g. '[UI] Female checkbox clicked successfully.'"""
    if not ui_actions_enabled():
        return
    with pytest_table_output_live():
        print(f"[UI] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Browser lifecycle ([Browser] — COMMONS_BROWSER_LOG)
# ---------------------------------------------------------------------------

_browser_log: Optional[bool] = None


def browser_log_enabled() -> bool:
    """Print browser launch, teardown, and navigation (on by default)."""
    global _browser_log
    if _browser_log is None:
        raw = os.environ.get("COMMONS_BROWSER_LOG", "1").strip().lower()
        _browser_log = raw not in ("0", "false", "no", "off")
    return _browser_log


def set_browser_log(on: bool) -> None:
    global _browser_log
    _browser_log = on


_console_needs_leading_newline = False


def prepare_test_live_console() -> None:
    """
    Pytest prints the test node id without a trailing newline; the first live
    console line in that test would otherwise appear on the same row.
    """
    global _console_needs_leading_newline
    _console_needs_leading_newline = True


def _live_console_line(msg: str) -> str:
    global _console_needs_leading_newline
    if _console_needs_leading_newline:
        _console_needs_leading_newline = False
        return f"\n{msg}"
    return msg


def browser_log(msg: str) -> None:
    if not browser_log_enabled():
        return
    with pytest_table_output_live():
        print(_live_console_line(f"[Browser] {msg}"), flush=True)


# ---------------------------------------------------------------------------
# Expected-data queries ([DB] — COMMONS_DB_QUERIES)
# ---------------------------------------------------------------------------

_db_queries: Optional[bool] = None


def db_queries_enabled() -> bool:
    """Print Memgraph Cypher to the console when executed (on by default)."""
    global _db_queries
    if _db_queries is None:
        raw = os.environ.get("COMMONS_DB_QUERIES", "1").strip().lower()
        _db_queries = raw not in ("0", "false", "no", "off")
    return _db_queries


def set_db_queries(on: bool) -> None:
    global _db_queries
    _db_queries = on


def memgraph_connection(user: str, server: str, output: str = "") -> None:
    say(f"Connection data for Memgraph is: user={user} output={output} server={server}")


def memgraph_query(label: str, query: str) -> None:
    if db_queries_enabled():
        with pytest_table_output_live():
            print(f"[DB] {label}:\n{query}", flush=True)
    elif enabled():
        say(f"This is the value of {label}:\n{query}")


def memgraph_db_row(cells: Sequence[str]) -> None:
    """Katalon ConnectNeo4jV4: System.out.println('Data STR:  '+str)"""
    line = "||".join(str(c) for c in cells) + "||"
    say(f"Data STR:  {line}")


def memgraph_db_table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    if header:
        say(f"DB header: {'||'.join(header)}||")
    for row in rows:
        memgraph_db_row(row)


# ---------------------------------------------------------------------------
# Filter labels (human-readable [UI] messages)
# ---------------------------------------------------------------------------


def filter_facet_display(group_key: str, facet_key: Optional[str] = None) -> str:
    if facet_key:
        return facet_key.replace("_Facet", "").replace("_", " ")
    return group_key.split("/")[0]


def _filter_token_display(token: str) -> str:
    """One underscore segment, e.g. dbGaP or SexAtBirth → display text for [UI] logs."""
    if token == "dbGaP":
        return "dbGaP"
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", token)


def filter_subfilter_display(group_key: str) -> str:
    tail = group_key.split("/")[-1] if "/" in group_key else group_key
    return " ".join(_filter_token_display(part) for part in tail.split("_"))


# ---------------------------------------------------------------------------
# Verbose UI / navigation (COMMONS_VERBOSE only)
# ---------------------------------------------------------------------------


def navigate(url: str) -> None:
    browser_log(f"Navigating to {url}")
    say(f"This is URL: {url}")


def click(repo_key: Optional[str], xpath: str) -> None:
    if repo_key:
        say(f"clickTab ({repo_key})")
    say(f"xpath: {xpath}")


def fill(xpath: str, text: str, repo_key: Optional[str] = None) -> None:
    if repo_key:
        say(f"fill ({repo_key})")
    say(f"xpath: {xpath}")
    say(f"text: {text}")


def xpath_info(label: str, xpath: str) -> None:
    say(f"This is the value of {label}: {xpath}")


def stat_bar(values: dict) -> None:
    say(f"Stat bar read: {values}")


# ---------------------------------------------------------------------------
# Stat bar (live + verbose)
# ---------------------------------------------------------------------------


def stat_bar_count_from_ui(name: str, value: str) -> None:
    """Katalon readStatBar*: 'This is the value of Participants count from Stat bar: …'"""
    with pytest_table_output_live():
        print(f"This is the value of {name} count from Stat bar: {value}", flush=True)


def stat_bar_count_from_db(name: str, value: str) -> None:
    """Katalon validateStatBar: 'This is the value of Participants Count from DB result: …'"""
    with pytest_table_output_live():
        print(f"This is the value of {name} Count from DB result: {value}", flush=True)


def multifunc_stat(stat_str: str, stat_int: int) -> None:
    say(f"This is the value of stat (string) obtained from multifunction: {stat_str}")
    say(f"This is the value of stat (integer) obtained from multifunction: {stat_int}")


# ---------------------------------------------------------------------------
# Result table read (headers, pages, rows)
# ---------------------------------------------------------------------------


def table_setup(tbl_xpath: str, body_xpath: str, hdr_xpath: str, next_xpath: str) -> None:
    say(f"This is the value of tbl main : {tbl_xpath}")
    say(f"This is the value of table body: {body_xpath}")
    say(f"This is the value of the xpath of nextbtn : {next_xpath}")
    say(f"This is the value of the hdr string - xpath : {hdr_xpath}")


def table_header_columns(columns: Sequence[str]) -> None:
    hdrdata = "||".join(columns) + ("||" if columns else "")
    say(f"Table header data: {hdrdata}")


def table_header_complete(app_key: str, hdr: Sequence[str], raw_th_count: int) -> None:
    """
    Katalon ReadCasesTableKatalon header pass (always printed, like System.out.println).

    Example::
        Inside C3DC switch case for header data:  12
        Number of columns in the current result tab is:  10
        Complete list of column headers in current tab:  Study||Participants||...
    """
    hdrdata = "||".join(str(h) for h in hdr) + ("||" if hdr else "")
    table_live_print(f"Inside {app_key} switch case for header data:  {raw_th_count}")
    table_live_print(f"Number of columns in the current result tab is:  {len(hdr)}")
    table_live_print(f"Complete list of column headers in current tab:  {hdrdata}")
    if enabled():
        say(f"Table header data: {hdrdata}")


def table_page_size(rows_on_page: int) -> None:
    say(f"This is the size of the rows in the results table in first page: {rows_on_page}")


def table_row_cells(row_index: int, cells: Sequence[str]) -> None:
    """One UI row, Katalon-style (cells joined with ||); verbose-only duplicate of table_reader prints."""
    data = "||".join(str(c) for c in cells) + "||"
    say(f"This is the value of data : {data}")


def table_page_rows(rows: Iterable[Sequence[str]], page: int = 1) -> None:
    for idx, cells in enumerate(rows, start=1):
        table_row_cells(idx, cells)
    say(f"COLLECTED DATA FROM PAGE - {page}")


def table_body_line(data: str) -> None:
    say(f"Table body data from current page is: {data}")


# ---------------------------------------------------------------------------
# Compare and skips
# ---------------------------------------------------------------------------


def compare_step(web_sheet: str, db_sheet: str) -> None:
    say(f"compareSheetsByRow({web_sheet}, {db_sheet})")


def skip_zero_stat() -> None:
    say("Skipping data collection from neo4j and compare lists of web and db as the stat value is 0")


def skip_zero_tab_count(tab_label: str = "") -> None:
    detail = f" ({tab_label})" if tab_label else ""
    say(
        "Skipping table read and DB compare — selected result tab count is 0"
        + detail
    )


def json_data_str(obj) -> None:
    say(f"Data STR:  {json.dumps(obj, separators=(',', ':'), ensure_ascii=False)}")
