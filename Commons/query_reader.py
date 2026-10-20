"""
Load Cypher/SQL queries from per-test Excel workbooks (InputFiles/<app>/TC*.xlsx).

Sheet 1 columns: TabName, TabQuery (or query), StatQuery, DbExcel / UIExcel (CTDC) or TsvExcel / WebExcel (legacy).
Each TabName row (e.g. ParticipantsTab) maps to the query run for that result tab.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import openpyxl

from Commons.settings import input_dir


@dataclass
class QueryFile:
    """Queries read from one test-case workbook."""
    path: Path
    queries_by_tab: Dict[str, str] = field(default_factory=dict)
    stat_bar_query: str = ""
    ui_output_workbook: str = ""   # WebExcel column, if present

    @property
    def name(self) -> str:
        return self.path.stem

    def tab_keys(self) -> List[str]:
        return sorted(self.queries_by_tab)

    def query_for_tab(self, tab_key: str) -> str:
        """Return the query for a TabName row (e.g. 'ParticipantsTab')."""
        try:
            return self.queries_by_tab[tab_key]
        except KeyError:
            raise KeyError(
                f"{self.path.name} has no query for tab '{tab_key}'. "
                f"Tabs in file: {self.tab_keys()}") from None


def read_query_file(app: str, file_name: str, root: Optional[Path] = None) -> QueryFile:
    """Read InputFiles/<app>/<file_name> and return tab-keyed queries."""
    path = Path(file_name)
    if not path.is_absolute():
        path = (root or input_dir(app)) / file_name
    if not path.is_file():
        raise FileNotFoundError(f"Query workbook not found: {path}")
    return _parse_workbook(path)


def _parse_workbook(path: Path) -> QueryFile:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        raise ValueError(f"Query workbook is empty: {path}")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    col = {h: i for i, h in enumerate(headers)}
    col.update({k.lower(): v for k, v in col.items() if k})
    query_col = col.get("TabQuery", col.get("query"))

    def cell(row, name: str) -> str:
        i = col.get(name) if name in col else col.get(name.lower())
        if i is None or i >= len(row) or row[i] is None:
            return ""
        return str(row[i]).strip()

    def cell_any(row, *names: str) -> str:
        for name in names:
            v = cell(row, name)
            if v:
                return v
        return ""

    doc = QueryFile(path=path)
    for row in rows[1:]:
        tab_key = cell(row, "TabName")
        if not tab_key:
            continue
        if query_col is not None and query_col < len(row) and row[query_col]:
            doc.queries_by_tab[tab_key] = str(row[query_col]).strip()
        if cell(row, "StatQuery") and not doc.stat_bar_query:
            doc.stat_bar_query = cell(row, "StatQuery")
        ui = cell_any(row, "UIExcel", "WebExcel")
        if ui and not doc.ui_output_workbook:
            doc.ui_output_workbook = ui
    return doc
