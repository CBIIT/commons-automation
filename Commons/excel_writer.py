"""Write UI and DB result tables to Excel under OutputFiles/<app>/<ENV>/ (gitignored)."""
from pathlib import Path
from typing import List, Sequence

import openpyxl

_ILLEGAL_SHEET_CHARS = "[]:*?/\\"


def write_sheet(path: Path, sheet: str, header: Sequence[str], rows: List[Sequence[str]]):
    """Create or update one worksheet (header + rows) in an .xlsx file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet = "".join("_" if c in _ILLEGAL_SHEET_CHARS else c for c in sheet)[:31]
    if path.exists():
        wb = openpyxl.load_workbook(path)
        if sheet in wb.sheetnames:
            del wb[sheet]
    else:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
    ws = wb.create_sheet(sheet)
    ws.append(list(header))
    for r in rows:
        ws.append([_safe(c) for c in r])
    wb.save(path)


def _safe(value):
    """openpyxl rejects control characters that innerText occasionally contains."""
    if isinstance(value, str):
        return "".join(ch for ch in value if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return value
