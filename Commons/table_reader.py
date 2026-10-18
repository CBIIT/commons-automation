"""
Read paginated Explore result tables from the browser.

Each app (GC, ICDC, C3DC, INS, Bento, CTDC) has its own column/xpath rules in
read_table_header_data and read_table_row_data. read_table_data loads headers, walks
pages via Next, and returns a Table for compare and excel_writer. Cell values print
live during the read while pytest capture is suspended.
"""
from __future__ import annotations

import os
import sys
import time
from typing import TYPE_CHECKING, List, Optional, Sequence

from Commons import action_log
from Commons.memgraph_source import Table

if TYPE_CHECKING:
    from Commons.apps.base import TabSpec
    from Commons.browser_actions import Ui

# Default column loop bounds; override with G_ROWCOUNT_FILES / G_ROWCOUNT_KATALON.
G_ROWCOUNT_FILES = int(os.environ.get("G_ROWCOUNT_FILES", "8"))
G_ROWCOUNT_KATALON = int(os.environ.get("G_ROWCOUNT_KATALON", "13"))

TABLE_APPS = frozenset({"GC", "ICDC", "C3DC", "INS", "Bento", "CTDC"})


def _inner_text(ui: "Ui", xpath: str) -> str:
    try:
        return ui.text(xpath).strip()
    except Exception:
        return ""


def _header_at(col_header: Sequence[str], j: int) -> str:
    if j < 0 or j >= len(col_header):
        return ""
    return col_header[j]


def _load_col_header(ui: "Ui", header_xpath: str) -> List[str]:
    action_log.say(f"This is the value of the hdr string - xpath : {header_xpath}")
    return [h.strip() for h in ui.header_texts(header_xpath)]


def _print_table_cell(header_name: str, value: str) -> None:
    """Log column header name and cell text for one table body cell."""
    action_log.table_live_print(f"This is the name of column header:  {header_name}")
    action_log.table_live_print(f"This is the value of  table  cell:  {value}")


def _keep_header(hdr: List[str], _c: int, name: str) -> None:
    hdr.append(name)


def read_table_header_data(app_key: str, tbl_main: str, col_header: Sequence[str]) -> List[str]:
    """Which UI columns to keep for this app/tab (skips Access, Manifest, etc.)."""
    hdr: List[str] = []
    n = len(col_header)

    if app_key == "GC":
        for c in range(1, n):
            _keep_header(hdr, c, _header_at(col_header, c))

    elif app_key == "ICDC":
        for c in range(n):
            text = _header_at(col_header, c)
            if text != "Access":
                _keep_header(hdr, c, text)

    elif app_key == "C3DC":
        if tbl_main in ("//*[@id='participant_tab_table']", "//*[@id='file_tab_table']"):
            for c in range(1, n):
                text = _header_at(col_header, c).strip()
                if text != "Available CPI Mapping":
                    _keep_header(hdr, c, text)
        else:
            for c in range(n):
                text = _header_at(col_header, c)
                if text != "Manifest":
                    _keep_header(hdr, c, text)

    elif app_key == "INS":
        for c in range(n):
            text = _header_at(col_header, c)
            if text not in ("Project(s)", "Program(s)"):
                _keep_header(hdr, c, text)

    elif app_key == "Bento":
        columns_count = n - 1
        for c in range(1, columns_count + 1):
            text = _header_at(col_header, c)
            if text != "Access":
                _keep_header(hdr, c, text)

    elif app_key == "CTDC":
        for c in range(1, n):
            text = _header_at(col_header, c)
            if text != "Access":
                _keep_header(hdr, c, text)

    else:
        raise ValueError(f"read_table_header_data: unsupported app_key {app_key!r}")

    if hdr:
        action_log.table_header_complete(app_key, hdr, n)
    return hdr


def read_table_row_data(
    app_key: str,
    ui: "Ui",
    *,
    tbl_main: str,
    tbl_bdy: str,
    row_index: int,
    col_header: Sequence[str],
    g_rowcount_files: int = G_ROWCOUNT_FILES,
    g_rowcount_katalon: int = G_ROWCOUNT_KATALON,
    first_child: bool = False,
    trace: bool = True,
) -> List[str]:
    """Read one tbody row: per-cell xpath rules, optional live header/cell console output."""
    parts: List[str] = []
    data = ""

    def add(value: str, header_j: int) -> None:
        nonlocal data
        if trace:
            _print_table_cell(_header_at(col_header, header_j), value)
        data += value + "||"
        parts.append(value)

    if app_key == "GC":
        tblcol = g_rowcount_files
        child = "/*[1]" if first_child else ""
        if tbl_main in ('//div[@id="case_tab_table"]', '//*[@id="case_tab_table"]'):
            tblcol = tblcol - 3
            for j in range(1, tblcol + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/*[{j + 1}]{child}"), j)
        elif tbl_main == '//*[@id="sample_tab_table"]':
            tblcol = tblcol - 3
            for j in range(1, tblcol + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/*[{j + 1}]{child}"), j)
        elif tbl_main == '//*[@id="file_tab_table"]':
            tblcol = tblcol - 2
            for j in range(1, tblcol + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/*[{j + 1}]{child}"), j)
        else:
            raise RuntimeError(f"Invalid tab for GC: {tbl_main}")

    elif app_key == "ICDC":
        tblcol = g_rowcount_katalon
        if tbl_main == "//*[@id='case_tab_table']":
            for j in range(2, tblcol + 1):
                hj = j - 2
                if _header_at(col_header, hj) == "Case ID":
                    add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j}]/div/a"), hj)
                else:
                    add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j}]"), hj)
        elif tbl_main == "//*[@id='sample_tab_table']":
            for j in range(2, tblcol + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j}]"), j - 2)
        elif tbl_main == "//*[@id='file_tab_table']":
            tblcol = tblcol - 2
            for j in range(0, tblcol):
                if _header_at(col_header, j) != "Access":
                    add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 2}]"), j)
        elif tbl_main == "//table":
            tblcol = tblcol - 5
            for j in range(0, tblcol):
                if _header_at(col_header, j) != "Access":
                    add(_inner_text(ui, f"{tbl_bdy}//tr[{row_index}]/td[{j + 2}]"), j)
        else:
            print("Invalid Tab! Could not read the tab (ICDC)", tbl_main, file=sys.stderr)

    elif app_key == "C3DC":
        tblcol = g_rowcount_files
        if tbl_main == "//*[@id='participant_tab_table']":
            tblcol = tblcol - 2
            for j in range(1, tblcol):
                if _header_at(col_header, j) != "Available CPI Mapping":
                    add(_inner_text(ui, f"{tbl_bdy}//tr[{row_index}]//td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='study_tab_table']":
            tblcol = tblcol + 5
            for j in range(0, tblcol):
                if _header_at(col_header, j) != "Manifest":
                    add(_inner_text(ui, f"{tbl_bdy}//tr[{row_index}]//td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='diagnosis_tab_table']":
            tblcol = tblcol - 1
            for j in range(0, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}//tr[{row_index}]//td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='genetic_analysis_tab_table']":
            tblcol = tblcol + 1
            for j in range(0, tblcol):
                if _header_at(col_header, j) != "Manifest":
                    add(_inner_text(ui, f"{tbl_bdy}//tr[{row_index}]//td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='treatment_tab_table']":
            tblcol = tblcol - 1
            for j in range(0, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='treatment_response_tab_table']":
            tblcol = tblcol - 2
            for j in range(1, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='survival_tab_table']":
            tblcol = tblcol - 3
            for j in range(0, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='sample_tab_table']":
            tblcol = tblcol - 1
            for j in range(0, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='file_tab_table']":
            tblcol = tblcol + 2
            for j in range(1, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        else:
            print("Check C3DC table data collection for tbl_main", tbl_main, file=sys.stderr)

    elif app_key == "INS":
        tblcol = g_rowcount_katalon
        if tbl_main == "//*[@id='program_tab_table']":
            tblcol = tblcol - 9
            for j in range(0, tblcol + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]//td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='project_tab_table']":
            tblcol = tblcol - 8
            for j in range(0, tblcol + 1):
                if _header_at(col_header, j) != "Program(s)":
                    add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]//td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='grant_tab_table']":
            tblcol = tblcol - 7
            for j in range(0, tblcol + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]//td[{j + 1}]"), j)
        elif tbl_main == "//*[@id='publication_tab_table']":
            tblcol = tblcol - 7
            for j in range(0, tblcol + 1):
                if _header_at(col_header, j) != "Project(s)":
                    add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]//td[{j + 1}]//p"), j)
        else:
            print("Check INS switch statment for this error", file=sys.stderr)

    elif app_key == "Bento":
        columns_count = len(col_header) - 1
        if tbl_main == '//*[@id="case_tab_table"]':
            for j in range(1, columns_count + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == '//*[@id="sample_tab_table"]':
            for j in range(1, columns_count + 1):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == '//*[@id="file_tab_table"]':
            for j in range(1, columns_count + 1):
                if _header_at(col_header, j) != "Access":
                    add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        else:
            raise RuntimeError("Invalid Tab name! Check Bento table data collection function")

    elif app_key == "CTDC":
        tblcol = g_rowcount_files
        if tbl_main == '//*[@id="participants_tab_table"]':
            tblcol = tblcol + 1
            for j in range(1, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == '//*[@id="biospecimens_tab_table"]':
            for j in range(1, tblcol):
                add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        elif tbl_main == '//*[@id="file_tab_table"]':
            tblcol = tblcol + 3
            for j in range(1, tblcol):
                if _header_at(col_header, j) != "Access":
                    add(_inner_text(ui, f"{tbl_bdy}/tr[{row_index}]/td[{j + 1}]"), j)
        else:
            print("Check CTDC switch statment for this error", file=sys.stderr)

    else:
        raise ValueError(f"read_table_row_data: unsupported app_key {app_key!r}")

    if data:
        action_log.table_body_line(data)
    return parts


def _read_table_body_page(
    ui: "Ui",
    tbl_bdy: str,
    tbl_main: str,
    app_key: str,
    col_header: Sequence[str],
    g_rowcount_files: int,
    g_rowcount_katalon: int,
    first_child: bool,
    trace: bool = True,
) -> List[List[str]]:
    """All data rows on the current page (trace=False when polling pagination only)."""
    row_loc = ui.loc(f"{tbl_bdy}//tr")
    rows_count = row_loc.count()
    action_log.table_page_size(rows_count)
    out: List[List[str]] = []
    for i in range(1, rows_count + 1):
        cells = read_table_row_data(
            app_key,
            ui,
            tbl_main=tbl_main,
            tbl_bdy=tbl_bdy,
            row_index=i,
            col_header=col_header,
            g_rowcount_files=g_rowcount_files,
            g_rowcount_katalon=g_rowcount_katalon,
            first_child=first_child,
            trace=trace,
        )
        action_log.table_row_cells(i, cells)
        out.append(cells)
    return out


def options_from_spec(spec: "TabSpec", default_max_pages: int) -> dict:
    """Map TabSpec fields to read_table_data kwargs (max_pages, first_page, first_child)."""
    return dict(
        max_pages=spec.max_pages if spec.max_pages is not None else default_max_pages,
        first_page=spec.first_page,
        first_child=spec.first_child,
    )


def _wait_for_pagination(ui: "Ui", next_xp: str, timeout_ms: int = 4000) -> None:
    try:
        ui.visible(next_xp).first.wait_for(state="visible", timeout=timeout_ms)
    except Exception:
        pass


def _rewind_to_first_page(ui: "Ui", next_xp: str, max_steps: int, page_reader) -> None:
    prev_xp = next_xp.replace("Next page", "Previous page")
    if prev_xp == next_xp:
        return
    for _ in range(max_steps):
        if not ui.is_visible(prev_xp):
            return
        prev = ui.visible(prev_xp).first
        if prev.get_attribute("disabled") is not None or prev.get_attribute("aria-disabled") == "true":
            return
        before = page_reader()
        ui.click(prev_xp)
        _wait_page_change(ui, page_reader, before)


def _wait_page_change(ui: "Ui", page_reader, previous: List[List[str]], timeout_s: float = 10.0) -> bool:
    end = time.time() + timeout_s
    while time.time() < end:
        now = page_reader()
        if now != previous:
            return True
        time.sleep(0.1)
    return False


def _advance_to_page(ui: "Ui", next_xp: str, page_reader, target_page: int) -> None:
    if target_page <= 1:
        return
    for _ in range(target_page - 1):
        if not ui.is_visible(next_xp):
            return
        nxt = ui.visible(next_xp).first
        if nxt.get_attribute("disabled") is not None or nxt.get_attribute("aria-disabled") == "true":
            return
        before = page_reader()
        ui.click(next_xp)
        if not _wait_page_change(ui, page_reader, before):
            return


def read_table_data(
    ui: "Ui",
    *,
    app_key: str,
    table_xpath: str,
    header_xpath: str,
    next_xpath: str,
    next_repo_key: str = "",
    max_pages: int = 10,
    first_page: int = 1,
    first_child: bool = False,
    g_rowcount_files: Optional[int] = None,
    g_rowcount_katalon: Optional[int] = None,
) -> Table:
    """Main entry: read header + paginated body for one results tab; returns UI Table."""
    if app_key not in TABLE_APPS:
        raise ValueError(f"read_table_data: app_key must be one of {sorted(TABLE_APPS)}, got {app_key!r}")

    tbl_main = table_xpath
    tbl_bdy = tbl_main + "//tbody"
    ui.wait_visible(tbl_bdy)
    action_log.table_setup(tbl_main, tbl_bdy, header_xpath, next_xpath)
    action_log.say(f"This is the value of tbl main : {tbl_main}")
    action_log.say(f"This is the value of table body: {tbl_bdy}")
    action_log.say(f"This is the value of the xpath of nextbtn : {next_xpath}")

    with action_log.pytest_table_output_live():
        col_header = _load_col_header(ui, header_xpath)
        rowcount_files = g_rowcount_files if g_rowcount_files is not None else G_ROWCOUNT_FILES
        rowcount_katalon = g_rowcount_katalon if g_rowcount_katalon is not None else G_ROWCOUNT_KATALON

        header = read_table_header_data(app_key, tbl_main, col_header)
        if not header:
            return Table()

        def page_reader(*, trace: bool = True) -> List[List[str]]:
            return _read_table_body_page(
                ui,
                tbl_bdy,
                tbl_main,
                app_key,
                col_header,
                rowcount_files,
                rowcount_katalon,
                first_child,
                trace=trace,
            )

        def page_reader_silent() -> List[List[str]]:
            return page_reader(trace=False)

        _wait_for_pagination(ui, next_xpath)
        _rewind_to_first_page(ui, next_xpath, max_pages, page_reader_silent)
        _advance_to_page(ui, next_xpath, page_reader_silent, first_page)

        rows: List[List[str]] = []
        last_page = first_page + max_pages - 1
        counter = first_page
        while counter <= last_page:
            page_rows = page_reader(trace=True)
            action_log.say(f"Number of rows per page is: {len(page_rows)}")
            action_log.say(f"COLLECTED DATA FROM PAGE - {counter}")
            rows.extend(page_rows)

            if counter >= last_page:
                break
            if not ui.is_visible(next_xpath):
                break
            nxt = ui.visible(next_xpath).first
            if nxt.get_attribute("disabled") is not None or nxt.get_attribute("aria-disabled") == "true":
                break
            action_log.say("Clicked next button")
            ui.click(next_xpath, repo_key=next_repo_key or None)
            if not _wait_page_change(ui, page_reader_silent, page_rows):
                break
            counter += 1

        return Table(header=header, rows=rows)
