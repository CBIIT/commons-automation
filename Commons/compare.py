"""
Compare what the UI shows against the expected data.

Katalon equivalent: ``Utils.compareSheetsByRow()`` → ``compareTwoLists()`` /
``normalizeSemicolonList()`` / ``stripCpiBadge()``.

Compare flow (matches Katalon):
  * Sort both sides by whole row (left-to-right column text).
  * Compare row-by-row at the same index; print each cell match or mismatch.
  * A cell matches if ``cells_match(ui, expected)`` (raw, CPI badge stripped, or normalized ``;`` lists).

Row count mismatch fails (Katalon silently passed when expected was empty; we still fail that case).
"""
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Sequence

from Commons import action_log

_MATCH = "\u2713"
_MISMATCH = "\u2717"
_ANSI_RED = "\033[31m"
_ANSI_RESET = "\033[0m"


def normalize_list(value: str) -> str:
    """'B; A ;C' -> 'A;B;C'. Order/spacing-insensitive form of a multi-value cell."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if ";" in s:
        items = [re.sub(r"\s+", " ", p.strip()) for p in s.split(";")]
        items = [p for p in items if p]
        items.sort(key=str.lower)
        return ";".join(items)
    return re.sub(r"\s+", " ", s)


def strip_cpi_badge(value: str) -> str:
    """Remove the CPI badge the UI appends to Participant IDs (e.g. 'ID123 2' or 'ID123\\n2')."""
    if value is None:
        return ""
    out = str(value).replace("\r", "\n").replace(" ", " ").strip()
    nl = out.find("\n")
    if nl >= 0:
        out = out[:nl].strip()
    out = re.sub(r"(?<=\s)\(\d{1,3}\)$", "", out)
    out = re.sub(r"(?<=\s)\[\d{1,3}\]$", "", out)
    out = re.sub(r"(?<=\s)\d{1,3}$", "", out)
    return out.strip()


def cells_match(ui: str, expected: str) -> bool:
    ui = "" if ui is None else str(ui)
    expected = "" if expected is None else str(expected)
    clean = strip_cpi_badge(ui)
    return ui == expected or clean == expected or normalize_list(clean) == normalize_list(expected)


def _cell_text(cell) -> str:
    if cell is None:
        return ""
    return str(cell).strip()


def _row_sort_key(row: Sequence[str]) -> tuple:
    """Katalon ``ROW_ORDER``: compare columns left to right."""
    return tuple(_cell_text(c) for c in row)


def _stderr_use_color() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    force = os.environ.get("FORCE_COLOR", "").strip().lower()
    if force in ("1", "true", "yes", "on"):
        return True
    return sys.stderr.isatty()


def _compare_live(msg: str, *, err: bool = False) -> None:
    """Katalon-style compare line (live under pytest via table reader wiring)."""
    if err:
        text = msg
        if _stderr_use_color():
            text = f"{_ANSI_RED}{msg}{_ANSI_RESET}"
        print(text, flush=True, file=sys.stderr)
    else:
        action_log.table_live_print(msg)


@dataclass
class Comparison:
    passed: bool
    ui_count: int
    expected_count: int
    problems: List[str] = field(default_factory=list)
    ui_only: List[Sequence[str]] = field(default_factory=list)
    expected_only: List[Sequence[str]] = field(default_factory=list)

    def summary(self, limit: int = 5) -> str:
        if self.passed:
            return f"OK ({self.ui_count} rows match)"
        lines = [f"UI rows={self.ui_count}, expected rows={self.expected_count}"] + self.problems
        for label, rows in (("only in UI", self.ui_only), ("only in expected data", self.expected_only)):
            if rows:
                lines.append(f"  {len(rows)} row(s) {label}; first {min(limit, len(rows))}:")
                lines += [f"    {' | '.join(map(str, r))}" for r in rows[:limit]]
        return "\n".join(lines)


def compare_tables(
    ui_rows: List[Sequence[str]],
    expected_rows: List[Sequence[str]],
    ui_header: Sequence[str] = (),
    expected_header: Sequence[str] = (),
) -> Comparison:
    """Compare data rows (headers excluded). Katalon ``compareTwoLists`` after row sort."""
    ui = [list(r) for r in ui_rows]
    exp = [list(r) for r in expected_rows]
    ui.sort(key=_row_sort_key)
    exp.sort(key=_row_sort_key)

    problems: List[str] = []
    ui_only: List[Sequence[str]] = []
    expected_only: List[Sequence[str]] = []

    with action_log.pytest_table_output_live():
        _compare_live("============== Verification of the data ==============")
        _compare_live(f"This is the row size of the UIWeb Output data: {len(ui)}")
        _compare_live(f"This is the row size of the TSV   Output data: {len(exp)}")

        if len(ui) != len(exp):
            problems.append("ROW COUNT MISMATCH")

        row_count = max(len(ui), len(exp))
        for idx in range(row_count):
            ui_row_num = idx + 2  # Katalon Excel row index (row 1 = header)
            db_row_num = idx + 2

            if idx >= len(ui):
                expected_only.append(exp[idx])
                if "DATA MISMATCH" not in problems:
                    problems.append("DATA MISMATCH")
                continue
            if idx >= len(exp):
                ui_only.append(ui[idx])
                if "DATA MISMATCH" not in problems:
                    problems.append("DATA MISMATCH")
                continue

            ui_row = ui[idx]
            exp_row = exp[idx]
            _compare_live(f"UI  Data Entire Row:  {ui_row}")
            _compare_live(f"TSV Data Entire Row:  {exp_row}")

            if len(ui_row) != len(exp_row):
                problems.append("COLUMN COUNT MISMATCH")
                _compare_live("*********** COLUMN COUNT MISMATCH ***********", err=True)
                _compare_live(
                    f"UI  Data Row: {ui_row_num} has {len(ui_row)} columns.", err=True
                )
                _compare_live(
                    f"TSV Data Row: {db_row_num} has {len(exp_row)} columns.", err=True
                )
                if ui_header or expected_header:
                    _compare_live(
                        f"UI header ({list(ui_header)}), DB header ({list(expected_header)})",
                        err=True,
                    )
                return Comparison(
                    False, len(ui_rows), len(expected_rows), problems, ui_only, expected_only
                )

            for col in range(len(exp_row)):
                ui_val = ui_row[col]
                db_val = exp_row[col]
                ui_s = "" if ui_val is None else str(ui_val)
                db_s = "" if db_val is None else str(db_val)
                ui_empty = ui_val is None or not ui_s.strip()
                db_empty = db_val is None or not db_s.strip()

                if ui_empty:
                    _compare_live(f"There is an empty cell in UI Data Row: {ui_row_num} Col: {col}")
                if db_empty:
                    _compare_live(
                        f"There is an empty cellin TSV Data Row: {db_row_num} Col: {col}"
                    )
                if ui_empty != db_empty:
                    _compare_live("********** EMPTY CELL MISMATCH **********", err=True)

                if cells_match(ui_s, db_s):
                    _compare_live(f"UI data cell value is:  {ui_s}\nDB data cell value is:  {db_s}")
                    _compare_live(
                        f"Content matches for Row: {ui_row_num} Col: {col} {_MATCH}"
                    )
                else:
                    if "DATA MISMATCH" not in problems:
                        problems.append("DATA MISMATCH")
                    _compare_live("*********** DATA MISMATCH ***********", err=True)
                    _compare_live(f"UI data cell value is:  {ui_s}\nDB data cell value is:  {db_s}", err=True)
                    _compare_live(
                        f"Content does not match for Row: {ui_row_num} Col: {col} {_MISMATCH}",
                        err=True,
                    )

    return Comparison(not problems, len(ui_rows), len(expected_rows), problems, ui_only, expected_only)


def compare_counts(ui_counts: dict, expected_counts: dict) -> Comparison:
    """Stat bar: {'Participants': '12', ...} both sides. Commas are ignored."""
    problems = []
    with action_log.pytest_table_output_live():
        for name, ui_val in ui_counts.items():
            exp_val = expected_counts.get(name)
            if exp_val is None:
                problems.append(f"Stat bar '{name}': no expected value")
                _compare_live(f"Stat bar '{name}': no expected value", err=True)
                continue
            if str(ui_val).replace(",", "").strip() != str(exp_val).replace(",", "").strip():
                problems.append(f"Stat bar '{name}' mismatch: UI={ui_val} expected={exp_val}")
                _compare_live(
                    f"Stat bar '{name}' mismatch: UI={ui_val} expected={exp_val}", err=True
                )
            else:
                _compare_live(f"Stat bar '{name}' matches: {ui_val} {_MATCH}")
    return Comparison(not problems, len(ui_counts), len(expected_counts), problems)
