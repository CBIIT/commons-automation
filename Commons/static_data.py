"""
Static marketing/info pages: compare UI text and links to InputFiles/<app>/*_StaticData.xlsx.
Each sheet (e.g. HomePage) lists object names, expected copy, and optional link URLs (QA host in file;
stage/prod URLs are derived when the object name contains Link).
"""
import re
from pathlib import Path
from typing import List, TYPE_CHECKING

import openpyxl

from Commons import excel_writer
from Commons.object_repository import LocatorNotFound
from Commons.settings import input_dir

if TYPE_CHECKING:
    from Commons.apps.base import BaseApp


# ---------------------------------------------------------------------------
# Text / URL normalization
# ---------------------------------------------------------------------------


def _normalize_text(text: str) -> str:
    """Collapse newlines and trim (UI inner_text vs Excel cell)."""
    return re.sub(r"\r?\n", " ", text or "").strip()


def _link_href_for_env(qa_href: str, env: str) -> str:
    """Map QA link from the sheet to the current test environment."""
    if env == "qa":
        return qa_href
    if env == "stage":
        return qa_href.replace("-qa", "-stage")
    return qa_href.replace("-qa", "")  # prod


# ---------------------------------------------------------------------------
# Static page verification (called from BaseApp.verify_static_data)
# ---------------------------------------------------------------------------


def verify_static_page(app: "BaseApp", sheet_name: str) -> List[str]:
    """Check one Excel sheet against Static/<sheet_name>/ locators; return failure messages (empty = pass)."""
    path = Path(input_dir(app.NAME)) / app.STATIC_DATA_EXCEL
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    if sheet_name not in wb.sheetnames:
        raise KeyError(f"Sheet '{sheet_name}' not in {path.name}. Sheets: {wb.sheetnames}")
    rows = list(wb[sheet_name].iter_rows(values_only=True))[1:]
    wb.close()

    problems: List[str] = []
    out_rows: List[list] = []
    for row in rows:
        if not row or not row[0]:
            continue
        obj = str(row[0]).strip()
        expected_text = _normalize_text(str(row[1]) if len(row) > 1 and row[1] is not None else "")
        expected_url = str(row[2]).strip() if len(row) > 2 and row[2] else ""
        ok = False
        try:
            xp = app.repo.xpath(f"Static/{sheet_name}/{obj}")
            el = app.ui.loc(xp).first
            el.wait_for(state="visible", timeout=10000)
            actual = _normalize_text(el.inner_text())
            text_ok = actual == expected_text
            if not text_ok:
                problems.append(f"{obj}: text is '{actual}', expected '{expected_text}'")
            url_ok = True
            if "Link" in obj:
                want = _link_href_for_env(expected_url, app.settings.env).replace("%20", " ")
                got = (el.get_attribute("href") or "").replace("%20", " ")
                url_ok = got == want
                if not url_ok:
                    problems.append(f"{obj}: link is '{got}', expected '{want}'")
            ok = text_ok and url_ok
        except LocatorNotFound as e:
            problems.append(f"{obj}: {e}")
        except Exception as e:
            problems.append(f"{obj}: element not found or not visible ({type(e).__name__})")
        out_rows.append([obj, expected_text, expected_url, str(ok).lower()])

    excel_writer.write_sheet(
        app.output_dir / f"Output_{app.STATIC_DATA_EXCEL}",
        sheet_name,
        ["Object", "Expected text", "Expected URL", "Passed"],
        out_rows,
    )
    return problems
