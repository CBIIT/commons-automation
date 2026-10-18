"""
Static page check (Katalon: TestRunner.verifyStaticData).

Reads <App>_StaticData.xlsx, one sheet per page (e.g. V_HomePage). Each row:

    object name | expected text | expected link URL (optional)

For every row the element  Static/<page>/<object name>  from the object repository must show the
expected text; objects whose name contains 'Link' must also point at the expected URL.
The URL in the sheet is the QA one; '-qa' is swapped for '-stage', or dropped for prod.
"""
import re
from pathlib import Path
from typing import List

import openpyxl

from Commons import excel_writer
from Commons.object_repository import LocatorNotFound
from Commons.settings import input_dir


def _one_line(text: str) -> str:
    return re.sub(r"\r?\n", " ", text or "").strip()


def _env_url(expected_url: str, env: str) -> str:
    if env == "qa":
        return expected_url
    if env == "stage":
        return expected_url.replace("-qa", "-stage")
    return expected_url.replace("-qa", "")          # prod


def verify_static_data(app, page_name: str) -> List[str]:
    """Returns a list of problems; empty means everything matched."""
    path = Path(input_dir(app.NAME)) / app.STATIC_DATA_EXCEL
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    if page_name not in wb.sheetnames:
        raise KeyError(f"Sheet '{page_name}' not in {path.name}. Sheets: {wb.sheetnames}")
    rows = list(wb[page_name].iter_rows(values_only=True))[1:]     # first row is the header
    wb.close()

    problems, out_rows = [], []
    for row in rows:
        if not row or not row[0]:
            continue
        obj = str(row[0]).strip()
        expected_text = _one_line(str(row[1]) if len(row) > 1 and row[1] is not None else "")
        expected_url = str(row[2]).strip() if len(row) > 2 and row[2] else ""
        ok = False
        try:
            xp = app.repo.xpath(f"Static/{page_name}/{obj}")
            el = app.ui.loc(xp).first
            el.wait_for(state="visible", timeout=10000)
            actual = _one_line(el.inner_text())
            text_ok = actual == expected_text
            if not text_ok:
                problems.append(f"{obj}: text is '{actual}', expected '{expected_text}'")
            url_ok = True
            if "Link" in obj:
                want = _env_url(expected_url, app.settings.env).replace("%20", " ")
                got = (el.get_attribute("href") or "").replace("%20", " ")
                url_ok = got == want
                if not url_ok:
                    problems.append(f"{obj}: link is '{got}', expected '{want}'")
            ok = text_ok and url_ok
        except LocatorNotFound as e:
            problems.append(f"{obj}: {e}")
        except Exception as e:      # element missing / not visible
            problems.append(f"{obj}: element not found or not visible ({type(e).__name__})")
        out_rows.append([obj, expected_text, expected_url, str(ok).lower()])

    excel_writer.write_sheet(app.output_dir / f"Output_{app.STATIC_DATA_EXCEL}", page_name,
                             ["Object", "Expected text", "Expected URL", "Passed"], out_rows)
    return problems
