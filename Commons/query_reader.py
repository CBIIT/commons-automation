"""
Read per-test query workbooks from InputFiles/<app>/ (usually TC*.xlsx).

First sheet: TabName, TabQuery (or query), StatQuery, optional UIExcel/WebExcel output names.
Tests load via BaseApp.load_query_file(); db_source runs the Cypher strings from here.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

import openpyxl

from Commons.settings import input_dir


# ---------------------------------------------------------------------------
# Parsed workbook (in memory for one test case)
# ---------------------------------------------------------------------------


@dataclass
class QueryFile:
    """Cypher (or legacy SQL) for stat bar and each result tab row in the Excel file."""

    path: Path
    queries_by_tab: Dict[str, str] = field(default_factory=dict)
    stat_bar_query: str = ""
    ui_output_workbook: str = ""  # UIExcel or WebExcel column, if present

    @property
    def name(self) -> str:
        return self.path.stem

    def tab_names(self) -> List[str]:
        """TabName values in the sheet (e.g. ParticipantsTab), sorted."""
        return sorted(self.queries_by_tab)

    def query_for_tab(self, tab_key: str) -> str:
        """Cypher for one TabName row (e.g. 'ParticipantsTab')."""
        try:
            return self.queries_by_tab[tab_key]
        except KeyError:
            raise KeyError(
                f"{self.path.name} has no query for tab '{tab_key}'. "
                f"Tabs in file: {self.tab_names()}"
            ) from None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_query_file(app: str, file_name: str, root: Optional[Path] = None) -> QueryFile:
    """Load InputFiles/<app>/<file_name> (or root override)."""
    path = Path(file_name)
    if not path.is_absolute():
        path = (root or input_dir(app)) / file_name
    if not path.is_file():
        raise FileNotFoundError(f"Query workbook not found: {path}")
    return _load_query_workbook(path)


# ---------------------------------------------------------------------------
# Excel parsing (private)
# ---------------------------------------------------------------------------


def _header_column_map(headers: Sequence[str]) -> Dict[str, int]:
    col = {h: i for i, h in enumerate(headers)}
    col.update({k.lower(): v for k, v in col.items() if k})
    return col


def _row_cell(row: Sequence, col: Mapping[str, int], column_name: str) -> str:
    i = col.get(column_name) if column_name in col else col.get(column_name.lower())
    if i is None or i >= len(row) or row[i] is None:
        return ""
    return str(row[i]).strip()


def _row_cell_first(row: Sequence, col: Mapping[str, int], *column_names: str) -> str:
    for name in column_names:
        value = _row_cell(row, col, name)
        if value:
            return value
    return ""


def _load_query_workbook(path: Path) -> QueryFile:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        raise ValueError(f"Query workbook is empty: {path}")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    col = _header_column_map(headers)
    query_col = col.get("TabQuery", col.get("query"))

    doc = QueryFile(path=path)
    for row in rows[1:]:
        tab_name = _row_cell(row, col, "TabName")
        if not tab_name:
            continue
        if query_col is not None and query_col < len(row) and row[query_col]:
            doc.queries_by_tab[tab_name] = str(row[query_col]).strip()
        if _row_cell(row, col, "StatQuery") and not doc.stat_bar_query:
            doc.stat_bar_query = _row_cell(row, col, "StatQuery")
        ui_name = _row_cell_first(row, col, "UIExcel", "WebExcel")
        if ui_name and not doc.ui_output_workbook:
            doc.ui_output_workbook = ui_name
    return doc
