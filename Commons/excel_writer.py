"""Write UI/DB compare tables to Excel under OutputFiles/<app>/<env>/ (gitignored)."""
import os
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Sequence, Set, Tuple

import openpyxl
from openpyxl.styles import Font, PatternFill

if TYPE_CHECKING:
    from Commons.compare import Comparison

# ---------------------------------------------------------------------------
# Sheet naming and styling
# ---------------------------------------------------------------------------

_ILLEGAL_SHEET_CHARS = "[]:*?/\\"
LISTING_HEADER_COLOR = "9BC2E6"
MISMATCH_FILL_COLOR = "FFC7CE"

# ---------------------------------------------------------------------------
# Write workbook
# ---------------------------------------------------------------------------


def excel_highlight_enabled() -> bool:
    """Set EXCEL_HIGHLIGHT_MISMATCH=0 to write plain workbooks (default: highlight on)."""
    v = os.environ.get("EXCEL_HIGHLIGHT_MISMATCH", "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def map_highlight_columns(
    cells: Set[Tuple[int, int]],
    narrow_keys: Sequence[str],
    full_header: Sequence[str],
) -> Set[Tuple[int, int]]:
    """Remap 0-based column indices from a narrow compare row onto a full header row."""
    out: Set[Tuple[int, int]] = set()
    for row_idx, col_idx in cells:
        if col_idx < len(narrow_keys):
            name = narrow_keys[col_idx]
            if name in full_header:
                out.add((row_idx, full_header.index(name)))
    return out


def highlight_sets_from_comparison(
    cmp: "Comparison",
    ui_column_count: int,
    expected_column_count: int,
) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    """Build per-workbook highlight coords from a table compare result."""
    ui_cells: Set[Tuple[int, int]] = set(cmp.mismatch_cells)
    db_cells: Set[Tuple[int, int]] = set(cmp.mismatch_cells)
    for row_idx in cmp.ui_extra_rows:
        for col in range(ui_column_count):
            ui_cells.add((row_idx, col))
    for row_idx in cmp.expected_extra_rows:
        for col in range(expected_column_count):
            db_cells.add((row_idx, col))
    return ui_cells, db_cells


def _apply_cell_highlights(ws, highlight_cells: Set[Tuple[int, int]]) -> None:
    if not highlight_cells or not excel_highlight_enabled():
        return
    fill = PatternFill(
        start_color=MISMATCH_FILL_COLOR,
        end_color=MISMATCH_FILL_COLOR,
        fill_type="solid",
    )
    for row_idx, col_idx in highlight_cells:
        if row_idx < 0 or col_idx < 0:
            continue
        ws.cell(row=row_idx + 2, column=col_idx + 1).fill = fill


def write_sheet(
    path: Path,
    sheet: str,
    header: Sequence[str],
    rows: List[Sequence[str]],
    header_color: Optional[str] = None,
    highlight_cells: Optional[Set[Tuple[int, int]]] = None,
) -> None:
    """Create or replace one worksheet (header + rows) in an .xlsx file."""
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
    if header_color:
        fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
        font = Font(bold=True, color="1F4E79")
        for cell in ws[1]:
            cell.fill = fill
            cell.font = font
    if highlight_cells:
        _apply_cell_highlights(ws, highlight_cells)
    wb.save(path)


# ---------------------------------------------------------------------------
# Cell values
# ---------------------------------------------------------------------------


def _safe(value):
    """openpyxl rejects control characters that innerText occasionally contains."""
    if isinstance(value, str):
        return "".join(ch for ch in value if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return value
