"""PSDC expected data from approved InputFiles/PSDC/<STUDY>/YYYY-MM-DD releases."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from Commons import action_log
from Commons.db_source import Table, format_db_cell
from Commons.query_reader import QueryFile
from Commons.settings import ROOT
from Commons.tab_setting import apply_tab_row_limit
from Commons.tsv_source import TsvSourceBackend, date_release_folders, tsv_tab_query_label


# These keys come from the PSDC loading templates, rather than CTDC's schema.
PSDC_NODE_INDEX = {
    "study": "study_short_name",
    "participant": "participant_id",
    "data_collection": "data_collection_record_id",
    "study_country": "study_country_record_id",
    "study_state_province_territory": "study_state_record_id",
    "study_personnel": "study_personnel_record_id",
    "publication": "publication_record_id",
    "associated_link": "associated_link_record_id",
    "file": "data_file_name",
}
PSDC_NODE_TABLE = {node: f"df_{node}" for node in PSDC_NODE_INDEX}


def psdc_node_for_filename(file_name: str) -> Optional[str]:
    """Recognize template names, including study.tsv.txt and transfer manifests."""
    name = Path(file_name).name.lower()
    if "file_transfer_manifest" in name:
        return "file"
    for node in sorted(PSDC_NODE_INDEX, key=len, reverse=True):
        if re.search(rf"(^|[\s_.-]){node}([\s_.-]|$)", name):
            return node
    return None


def load_psdc_merged_frames(tsv_root: Path) -> dict[str, pd.DataFrame]:
    """Merge releases oldest first, preserving study-scoped participant and file IDs.

    ZIP bundles are staging material: they can contain superseded data. Only
    explicitly selected files in dated study folders become expected data.
    """
    tsv_root = Path(tsv_root)
    if not tsv_root.is_dir():
        raise RuntimeError(f"PSDC TSV folder not found: {tsv_root}")
    versions = date_release_folders(tsv_root)
    if not versions:
        raise RuntimeError(
            f"No dated PSDC releases under {tsv_root}. "
            "Add approved TSV/TXT files to <STUDY>/YYYY-MM-DD/. ZIPs are not loaded automatically."
        )
    frames = {}
    for version in versions:
        study = version.parent.name
        seen = set()
        for path in sorted(version.rglob("*")):
            if path.suffix.lower() not in (".tsv", ".txt") or not path.is_file():
                continue
            if any(part.startswith(".") or part == "__MACOSX" for part in path.relative_to(version).parts):
                continue
            node = psdc_node_for_filename(path.name)
            if node is None:
                raise ValueError(f"Unrecognized PSDC node file: {path}")
            df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")
            df.columns = df.columns.str.strip()
            key = PSDC_NODE_INDEX[node]
            if key not in df.columns:
                raise ValueError(f"PSDC {path.name} is missing key column {key!r}")
            if df[key].str.strip().eq("").any():
                raise ValueError(f"PSDC {path.name} contains blank {key} values")
            if node == "study":
                keys = [key]
                if not df[key].eq(study).all():
                    raise ValueError(f"PSDC study values in {path} must match folder {study!r}")
            else:
                # The NLST participant export omits the study relationship.
                relationship = "study.study_short_name"
                if relationship not in df.columns:
                    df[relationship] = study
                df[relationship] = df[relationship].replace("", study)
                if not df[relationship].eq(study).all():
                    raise ValueError(f"PSDC study values in {path} must match folder {study!r}")
                keys = [relationship, key]
            if df.duplicated(keys).any():
                raise ValueError(f"Duplicate PSDC {node} keys in {path}")
            # Reject overlapping source files within a release; don't let an old
            # export silently overwrite another export of the same records.
            identities = {(node, tuple(row)) for row in df[keys].itertuples(index=False, name=None)}
            if seen.intersection(identities):
                raise ValueError(f"Overlapping PSDC {node} files in release {version}")
            seen.update(identities)
            if node in frames:
                df = pd.concat([frames[node], df], ignore_index=True).drop_duplicates(keys, keep="last")
            frames[node] = df
        action_log.say(f"PSDC TSV loaded for release: {study}/{version.name}")
    if "study" not in frames or frames["study"].empty:
        raise ValueError("PSDC releases must include a nonempty study TSV")
    return frames


class PsdcTsvSource(TsvSourceBackend):
    """Run the same Excel TabQuery / StatQuery flow used by CTDC."""

    def __init__(self, tsv_root: str = "", tab_row_limit: Optional[int] = None):
        root = Path(tsv_root or "InputFiles/PSDC")
        self._tsv_root = root if root.is_absolute() else ROOT / root
        self._tab_row_limit = tab_row_limit
        self._conn = None

    def _ensure_sqlite(self) -> sqlite3.Connection:
        if self._conn is None:
            frames = load_psdc_merged_frames(self._tsv_root)
            conn = sqlite3.connect(":memory:")
            try:
                for node, frame in frames.items():
                    frame.to_sql(PSDC_NODE_TABLE[node], conn, index=False, if_exists="replace")
            except Exception:
                conn.close()
                raise
            self._conn = conn
        return self._conn

    def run_sql_as_table(self, sql: str, query_label: str = "tab query from tsv") -> Table:
        action_log.memgraph_query(query_label, sql)
        cur = self._ensure_sqlite().execute(sql)
        table = Table(
            header=[column[0] for column in cur.description] if cur.description else [],
            rows=[[format_db_cell(value) for value in row] for row in cur.fetchall()],
        )
        action_log.memgraph_db_table(table.header, table.rows)
        return table

    def fetch_tab_table(self, query_file: QueryFile, tab_key: str,
                        tab_display_name: Optional[str] = None, apply_row_limit: bool = True) -> Table:
        sql = query_file.query_for_tab(tab_key)
        if apply_row_limit:
            sql = apply_tab_row_limit(sql, self._tab_row_limit)
        return self.run_sql_as_table(sql, tsv_tab_query_label(tab_key, tab_display_name))

    def fetch_stat_bar_table(self, query_file: QueryFile) -> Table:
        if not query_file.stat_bar_query:
            raise ValueError(f"{query_file.path.name} has no StatQuery")
        return self.run_sql_as_table(query_file.stat_bar_query, "Stat bar query from tsv")

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
