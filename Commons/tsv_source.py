"""
CTDC expected data from TSV/TXT node files (Katalon PythonFiles/CTDC/Utils.py).

Not used by C3DC, GC, ICDC, or CCDI. When CTDC moves to Memgraph, flip
`expected_source` in Config/environments.yaml and delete this module.

What this does, in order:
  1. Find dated folders under each study (tsv/CMB/2025-10-23, tsv/AHEP0731/2026-10-22)
     or directly under the TSV root (older layout).
  2. Load each node file (program, study, participant, …) into a DataFrame.
  3. If the same id appears in a newer folder, the newer row wins.
  4. Register the frames as SQLite tables named df_study, df_participant, …
     so the SQL in InputFiles/CTDC/TC*.xlsx runs as it did in Katalon.
  5. Return header + rows for compare (same Table type as Memgraph/Neo4j).
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from Commons import action_log
from Commons.db_source import ExpectedDataSource, Table, format_db_cell
from Commons.query_reader import QueryFile
from Commons.settings import ROOT
from Commons.tab_setting import apply_tab_row_limit


# Node token in the filename → index column in that TSV (Katalon index_columns).
# Example: CMB_v1.1_participant_8-18-25.tsv uses participant_id as the row key.
NODE_INDEX: Dict[str, str] = {
    "program": "program_short_name",
    "study": "study_id",
    "participant": "participant_id",
    "diagnosis": "diagnosis_record_id",
    "demographic": "demographic_record_id",
    "specimen": "specimen_record_id",
    "exposure": "exposure_record_id",
    "targeted_therapy": "targeted_therapy_record_id",
    "non_targeted_therapy": "non_targeted_therapy_record_id",
    "participant_status": "participant_status_record_id",
    "file": "data_file_uuid",
}

# SQL table names Katalon pandasql used (globals() in Utils.py).
# specimen files become df_biospecimen — the Excel queries say FROM df_biospecimen.
NODE_TABLE: Dict[str, str] = {
    "program": "df_program",
    "study": "df_study",
    "participant": "df_participant",
    "diagnosis": "df_diagnosis",
    "demographic": "df_demographic",
    "specimen": "df_biospecimen",
    "exposure": "df_exposure",
    "targeted_therapy": "df_targeted_therapy",
    "non_targeted_therapy": "df_non_targeted_therapy",
    "participant_status": "df_participant_status",
    "file": "df_file",
}

_DATE_FOLDER = "%Y-%m-%d"


def tsv_tab_query_label(tab_key: str, display_name: Optional[str] = None) -> str:
    """Console label for [DB] … when running a result-tab SQL query."""
    name = (display_name or "").strip()
    if not name:
        name = tab_key[:-3] if tab_key.endswith("Tab") else tab_key
    return f"{name} tab query from tsv"


def _is_date_folder(name: str) -> bool:
    try:
        datetime.strptime(name, _DATE_FOLDER)
        return True
    except ValueError:
        return False


def _node_for_filename(file_name: str) -> Optional[str]:
    """Pick the longest node token in the file name so 'participant' does not steal participant_status."""
    stem = Path(file_name).stem.lower()
    for node in sorted(NODE_INDEX, key=len, reverse=True):
        # CMB_v1_study_8-18-25.tsv and 59eb273a-…-study.tsv
        if re.search(rf"(^|_|-){re.escape(node)}(_|-|$)", stem):
            return node
    return None


def load_tsv_file(file_path: Path, index_column: str) -> Optional[pd.DataFrame]:
    """Read one TSV/TXT. Index column is the row key used when a later release updates a record."""
    try:
        df = pd.read_csv(file_path, delimiter="\t", index_col=index_column)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, KeyError, OSError) as exc:
        action_log.say(f"TSV skip {file_path.name}: {exc}")
        return None
    df.columns = df.columns.str.strip()
    return df


def _date_release_folders(tsv_root: Path) -> List[Path]:
    """YYYY-MM-DD folders: tsv/CMB/2025-10-23 and tsv/AHEP0731/2026-10-22, or tsv/2025-10-23."""
    found: List[Path] = []
    for child in tsv_root.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if _is_date_folder(child.name):
            found.append(child)
            continue
        for sub in child.iterdir():
            if sub.is_dir() and not sub.name.startswith(".") and _is_date_folder(sub.name):
                found.append(sub)
    found.sort(key=lambda path: (datetime.strptime(path.name, _DATE_FOLDER), path.parent.name))
    return found


def load_and_merge_versions(tsv_root: Path) -> Dict[str, pd.DataFrame]:
    """
    Walk YYYY-MM-DD folders oldest → newest (per study folder, then by date).

    Same id in a newer folder replaces the older row (Katalon load_and_merge_versions).
    """
    frames: Dict[str, pd.DataFrame] = {node: pd.DataFrame() for node in NODE_INDEX}
    if not tsv_root.is_dir():
        raise RuntimeError(
            f"CTDC TSV folder not found: {tsv_root}. "
            "Use InputFiles/CTDC/tsv/<STUDY>/YYYY-MM-DD/ or set CTDC_TSV_ROOT."
        )
    versions = _date_release_folders(tsv_root)
    if not versions:
        raise RuntimeError(
            f"No YYYY-MM-DD folders under {tsv_root}. "
            "Add InputFiles/CTDC/tsv/CMB/2025-10-23/ (and other studies the same way)."
        )
    for version_path in versions:
        version = f"{version_path.parent.name}/{version_path.name}"
        for file_name in version_path.iterdir():
            if file_name.suffix.lower() not in (".tsv", ".txt"):
                continue
            node = _node_for_filename(file_name.name)
            if node is None:
                continue
            df_new = load_tsv_file(file_name, NODE_INDEX[node])
            if df_new is None:
                continue
            current = frames[node]
            if not current.empty:
                overlap = df_new.index.intersection(current.index)
                for idx in overlap:
                    if not df_new.loc[idx].equals(current.loc[idx]):
                        current.loc[idx] = df_new.loc[idx]
                df_new = df_new[~df_new.index.isin(current.index)]
            frames[node] = pd.concat([current, df_new])
        action_log.say(f"Data successfully loaded for release: {version}")
    return frames


def _frames_to_sqlite(frames: Dict[str, pd.DataFrame]) -> sqlite3.Connection:
    """In-memory SQLite with Katalon table names (df_study, df_biospecimen, …)."""
    conn = sqlite3.connect(":memory:")
    for node, df in frames.items():
        table = NODE_TABLE[node]
        if df.empty:
            out = pd.DataFrame(columns=[NODE_INDEX[node]] + list(df.columns))
        else:
            out = df.reset_index()
        out.to_sql(table, conn, index=False, if_exists="replace")
    return conn


class TsvSource(ExpectedDataSource):
    """CTDC only: run TabQuery / StatQuery SQL against the TSV snapshot."""

    def __init__(
        self,
        tsv_root: str,
        app: str = "CTDC",
        tab_row_limit: Optional[int] = None,
    ):
        root = Path(tsv_root) if tsv_root else ROOT / "InputFiles" / "CTDC" / "tsv"
        if not root.is_absolute():
            root = ROOT / root
        self._tsv_root = root
        self._app = app
        self._tab_row_limit = tab_row_limit
        self._conn: Optional[sqlite3.Connection] = None
        self._logged_load = False

    def _ensure_loaded(self) -> sqlite3.Connection:
        if self._conn is None:
            frames = load_and_merge_versions(self._tsv_root)
            self._conn = _frames_to_sqlite(frames)
            if not self._logged_load:
                action_log.say(f"TSV expected data loaded from {self._tsv_root}")
                self._logged_load = True
        return self._conn

    def run_sql_as_table(self, sql: str, query_label: str = "tab query from tsv") -> Table:
        action_log.memgraph_query(query_label, sql)
        conn = self._ensure_loaded()
        cur = conn.execute(sql)
        header = [col[0] for col in cur.description] if cur.description else []
        rows = [[format_db_cell(value) for value in row] for row in cur.fetchall()]
        table = Table(header=header, rows=rows)
        action_log.memgraph_db_table(table.header, table.rows)
        return table

    def fetch_tab_table(
        self,
        query_file: QueryFile,
        tab_key: str,
        tab_display_name: Optional[str] = None,
        apply_row_limit: bool = True,
    ) -> Table:
        raw = query_file.query_for_tab(tab_key)
        sql = apply_tab_row_limit(raw, self._tab_row_limit) if apply_row_limit else raw
        return self.run_sql_as_table(sql, tsv_tab_query_label(tab_key, tab_display_name))

    def fetch_stat_bar_table(self, query_file: QueryFile) -> Table:
        if not query_file.stat_bar_query:
            raise ValueError(f"{query_file.path.name} has no StatQuery")
        return self.run_sql_as_table(query_file.stat_bar_query, "Stat bar query from tsv")

    def close_connection(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def close(self):
        self.close_connection()
