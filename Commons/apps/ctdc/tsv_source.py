"""CTDC expected data: dated node TSVs under InputFiles/CTDC/<STUDY>/YYYY-MM-DD/."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from Commons import action_log
from Commons.db_source import Table, format_db_cell
from Commons.query_reader import QueryFile
from Commons.settings import ROOT
from Commons.tab_setting import apply_tab_row_limit
from Commons.tsv_source import (
    TsvSourceBackend,
    date_release_folders,
    frames_to_sqlite,
    merge_all_tsv_versions,
    tsv_tab_query_label,
)

CTDC_DEFAULT_TSV_ROOT = "InputFiles/CTDC"

# ---------------------------------------------------------------------------
# CTDC node files
# ---------------------------------------------------------------------------

CTDC_NODE_INDEX: Dict[str, str] = {
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

CTDC_NODE_TABLE: Dict[str, str] = {
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

# Backward-compatible aliases (tests and docs)
NODE_INDEX = CTDC_NODE_INDEX
NODE_TABLE = CTDC_NODE_TABLE


def ctdc_node_for_filename(file_name: str) -> Optional[str]:
    """Match node token in CTDC TSV filename (longest token wins)."""
    stem = Path(file_name).stem.lower()
    for node in sorted(CTDC_NODE_INDEX, key=len, reverse=True):
        if re.search(rf"(^|_|-){re.escape(node)}(_|-|$)", stem):
            return node
    return None


def _ctdc_loaded_log(version: str) -> None:
    action_log.say(f"CTDC TSV loaded for release: {version}")


def ctdc_release_folders(tsv_root: Path) -> List[Path]:
    versions = date_release_folders(tsv_root)
    if not versions:
        raise RuntimeError(
            f"No YYYY-MM-DD folders under {tsv_root}. "
            "Add InputFiles/CTDC/CMB/2025-10-23/ (and other studies the same way)."
        )
    return versions


def resolve_ctdc_tsv_root(tsv_root: str) -> Path:
    root = Path(tsv_root) if tsv_root else ROOT / CTDC_DEFAULT_TSV_ROOT
    if not root.is_absolute():
        root = ROOT / root
    return root


def load_ctdc_merged_frames(tsv_root: Path) -> Dict[str, pd.DataFrame]:
    """Load and merge all CTDC dated TSV releases under tsv_root."""
    if not tsv_root.is_dir():
        raise RuntimeError(
            f"CTDC TSV folder not found: {tsv_root}. "
            "Use InputFiles/CTDC/<STUDY>/YYYY-MM-DD/ or set CTDC_TSV_ROOT."
        )
    versions = ctdc_release_folders(tsv_root)
    return merge_all_tsv_versions(
        tsv_root,
        versions,
        CTDC_NODE_INDEX,
        ctdc_node_for_filename,
        _ctdc_loaded_log,
    )


def load_and_merge_versions(tsv_root: Path) -> Dict[str, pd.DataFrame]:
    """CTDC entry point (tests and legacy callers)."""
    return load_ctdc_merged_frames(tsv_root)


class CtdcTsvSource(TsvSourceBackend):
    """Run TabQuery / StatQuery SQL from Excel against merged CTDC TSV snapshots."""

    def __init__(self, tsv_root: str = "", tab_row_limit: Optional[int] = None):
        self._tsv_root = resolve_ctdc_tsv_root(tsv_root)
        self._tab_row_limit = tab_row_limit
        self._conn: Optional[sqlite3.Connection] = None
        self._logged_load = False

    def _ensure_sqlite(self) -> sqlite3.Connection:
        if self._conn is None:
            frames = load_ctdc_merged_frames(self._tsv_root)
            self._conn = frames_to_sqlite(frames, CTDC_NODE_INDEX, CTDC_NODE_TABLE)
            if not self._logged_load:
                action_log.say(f"CTDC TSV expected data loaded from {self._tsv_root}")
                self._logged_load = True
        return self._conn

    def run_sql_as_table(self, sql: str, query_label: str = "tab query from tsv") -> Table:
        action_log.memgraph_query(query_label, sql)
        conn = self._ensure_sqlite()
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

    def close_connection(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def close(self) -> None:
        self.close_connection()
