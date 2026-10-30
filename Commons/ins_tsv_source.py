"""
INS expected data from dated TSV snapshots (Katalon PythonFiles/INS/Utils.py).

Tables: df_program, df_project, df_grant, df_publication — SQL in InputFiles/INS/TC*.xlsx.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from Commons import action_log
from Commons.db_source import ExpectedDataSource, Table, format_db_cell
from Commons.query_reader import QueryFile
from Commons.settings import ROOT
from Commons.tab_setting import apply_tab_row_limit
from Commons.ins_tsv_bundles import ensure_ins_tsv_bundles, ins_tsv_release_paths
from Commons.tsv_source import load_tsv_file, tsv_tab_query_label

import sqlite3

INS_NODE_INDEX: Dict[str, str] = {
    "program": "program_id",
    "project": "project_id",
    "grant": "grant_id",
    "publication": "pmid",
    "cedcd": "dataset_uuid",
    "dbgap": "dataset_uuid",
    "geo": "dataset_uuid",
}

INS_NODE_TABLE: Dict[str, str] = {
    "program": "df_program",
    "project": "df_project",
    "grant": "df_grant",
    "publication": "df_publication",
    "cedcd": "df_cedcd",
    "dbgap": "df_dbgap",
    "geo": "df_geo",
}


def _node_for_filename(file_name: str) -> Optional[str]:
    stem = Path(file_name).stem.lower()
    if "cedcd" in stem:
        return "cedcd"
    if "dbgap" in stem:
        return "dbgap"
    if "geo" in stem and "dataset" in stem:
        return "geo"
    for node in sorted(INS_NODE_INDEX, key=len, reverse=True):
        if node in stem:
            return node
    return None


def load_ins_tsv_versions(tsv_root: Path) -> Dict[str, pd.DataFrame]:
    """Merge dated folders and zip bundles under InputFiles/INS/ (Programs.zip, DataSetsTab.zip)."""
    frames: Dict[str, pd.DataFrame] = {node: pd.DataFrame() for node in INS_NODE_INDEX}
    if not tsv_root.is_dir():
        raise RuntimeError(
            f"INS TSV folder not found: {tsv_root}. "
            "Add InputFiles/INS/Programs.zip and DataSetsTab.zip (extracted automatically at run time)."
        )
    ensure_ins_tsv_bundles(tsv_root)
    versions = list(ins_tsv_release_paths(tsv_root))
    if not versions:
        versions = [tsv_root]
    for version_path in versions:
        if version_path == tsv_root:
            label = tsv_root.name
        elif version_path.parent == tsv_root:
            label = version_path.name
        else:
            label = f"{version_path.parent.name}/{version_path.name}"
        for file_name in version_path.iterdir():
            if file_name.suffix.lower() not in (".tsv", ".txt"):
                continue
            node = _node_for_filename(file_name.name)
            if node is None:
                continue
            df_new = load_tsv_file(file_name, INS_NODE_INDEX[node])
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
        action_log.say(f"INS TSV loaded for release: {label}")
    return frames


def _frames_to_sqlite(frames: Dict[str, pd.DataFrame]) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for node, df in frames.items():
        table = INS_NODE_TABLE[node]
        if df.empty:
            out = pd.DataFrame(columns=[INS_NODE_INDEX[node]] + list(df.columns))
        else:
            out = df.reset_index()
        out.to_sql(table, conn, index=False, if_exists="replace")
    return conn


class InsTsvSource(ExpectedDataSource):
    """Run INS TabQuery / StatQuery SQL against program/project/grant/publication TSVs."""

    def __init__(
        self,
        tsv_root: str,
        app: str = "INS",
        tab_row_limit: Optional[int] = None,
    ):
        root = Path(tsv_root) if tsv_root else ROOT / "InputFiles" / "INS"
        if not root.is_absolute():
            root = ROOT / root
        self._tsv_root = root
        self._app = app
        self._tab_row_limit = tab_row_limit
        self._conn: Optional[sqlite3.Connection] = None
        self._logged_load = False

    def _ensure_loaded(self) -> sqlite3.Connection:
        if self._conn is None:
            frames = load_ins_tsv_versions(self._tsv_root)
            self._conn = _frames_to_sqlite(frames)
            if not self._logged_load:
                action_log.say(f"INS TSV expected data loaded from {self._tsv_root}")
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
