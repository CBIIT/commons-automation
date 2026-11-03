"""
Expected tab/stat data from dated TSV snapshots (Katalon Utils.py pattern).

Shared load/merge/SQLite pipeline plus app wiring:
  - Commons.apps.ctdc.tsv_source — CTDC node TSVs, CtdcTsvSource
  - Commons.apps.ins.tsv_source  — INS Programs + DataSets, InsTsvSource

Use ``TsvSource(app=...)`` for expected_source: tsv, or import app modules directly
(e.g. ``from Commons.apps.ins.tsv_source import load_ins_dataset_frames``).
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import pandas as pd

from Commons import action_log
from Commons.db_source import ExpectedDataSource

AppName = str

# ---------------------------------------------------------------------------
# Shared TSV load / merge / SQLite (CTDC + INS)
# ---------------------------------------------------------------------------


class TsvSourceBackend(ExpectedDataSource):
    """Base type for CTDC/INS TSV expected-data sources (CtdcTsvSource, InsTsvSource)."""


DATE_FOLDER_FMT = "%Y-%m-%d"
DATE_ZIP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}\.zip$", re.I)


def tsv_tab_query_label(tab_key: str, display_name: Optional[str] = None) -> str:
    """Label for action logs when running tab SQL against TSV-backed SQLite."""
    name = (display_name or "").strip()
    if not name:
        name = tab_key[:-3] if tab_key.endswith("Tab") else tab_key
    return f"{name} tab query from tsv"


def load_tsv_file(file_path: Path, index_column: str) -> Optional[pd.DataFrame]:
    """Read one TSV/TXT; index column is the merge key. Skips bad files (logged)."""
    try:
        df = pd.read_csv(file_path, delimiter="\t", index_col=index_column)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, KeyError, OSError) as exc:
        action_log.say(f"TSV skip {file_path.name}: {exc}")
        return None
    df.columns = df.columns.str.strip()
    return df


def is_date_folder(name: str) -> bool:
    try:
        datetime.strptime(name, DATE_FOLDER_FMT)
        return True
    except ValueError:
        return False


def date_release_folders(tsv_root: Path) -> List[Path]:
    """YYYY-MM-DD dirs: STUDY/2025-10-23 or flat 2025-10-23, oldest → newest."""
    found: List[Path] = []
    for child in tsv_root.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if is_date_folder(child.name):
            found.append(child)
            continue
        for sub in child.iterdir():
            if sub.is_dir() and not sub.name.startswith(".") and is_date_folder(sub.name):
                found.append(sub)
    found.sort(key=lambda path: (datetime.strptime(path.name, DATE_FOLDER_FMT), path.parent.name))
    return found


def merge_row(current: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    """Same index updates in place, then append new ids."""
    if current.empty:
        return df_new
    overlap = df_new.index.intersection(current.index)
    for idx in overlap:
        if not df_new.loc[idx].equals(current.loc[idx]):
            current.loc[idx] = df_new.loc[idx]
    df_new = df_new[~df_new.index.isin(current.index)]
    return pd.concat([current, df_new])


def release_folder_label(version_path: Path, tsv_root: Path) -> str:
    if version_path == tsv_root:
        return version_path.name
    return f"{version_path.parent.name}/{version_path.name}"


def merge_all_tsv_versions(
    tsv_root: Path,
    version_folders: List[Path],
    node_index: Dict[str, str],
    node_for_filename: Callable[[str], Optional[str]],
    log_loaded: Callable[[str], None],
) -> Dict[str, pd.DataFrame]:
    """Merge dated TSV snapshots (oldest → newest): one DataFrame per node type."""
    frames: Dict[str, pd.DataFrame] = {node: pd.DataFrame() for node in node_index}
    for version_path in version_folders:
        for file_path in version_path.iterdir():
            if file_path.suffix.lower() not in (".tsv", ".txt"):
                continue
            node = node_for_filename(file_path.name)
            if node is None:
                continue
            df_new = load_tsv_file(file_path, node_index[node])
            if df_new is None:
                continue
            frames[node] = merge_row(frames[node], df_new)
        log_loaded(release_folder_label(version_path, tsv_root))
    return frames


def frames_to_sqlite(
    frames: Dict[str, pd.DataFrame],
    node_index: Dict[str, str],
    node_table: Dict[str, str],
) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for node, df in frames.items():
        table = node_table[node]
        if df.empty:
            out = pd.DataFrame(columns=[node_index[node]] + list(df.columns))
        else:
            out = df.reset_index()
        out.to_sql(table, conn, index=False, if_exists="replace")
    return conn


# Legacy private names (tests and older callers)
_date_release_folders = date_release_folders


def _node_for_filename(file_name: str) -> Optional[str]:
    from Commons.apps.ctdc.tsv_source import ctdc_node_for_filename

    return ctdc_node_for_filename(file_name)


def load_merged_frames(tsv_root: Path, app: AppName = "CTDC") -> Dict[str, pd.DataFrame]:
    """Load and merge all TSV releases for CTDC or INS Programs nodes."""
    if app == "CTDC":
        from Commons.apps.ctdc.tsv_source import load_ctdc_merged_frames

        return load_ctdc_merged_frames(tsv_root)
    if app == "INS":
        from Commons.apps.ins.tsv_source import load_ins_program_frames

        return load_ins_program_frames(tsv_root)
    raise ValueError(
        f"TSV expected data is not configured for app '{app}'. Supported: CTDC, INS."
    )


class TsvSource:
    """Factory: returns ``CtdcTsvSource`` or ``InsTsvSource`` for ``expected_source: tsv``."""

    def __new__(
        cls,
        tsv_root: str = "",
        app: AppName = "CTDC",
        tab_row_limit: Optional[int] = None,
    ) -> Union["CtdcTsvSource", "InsTsvSource"]:
        if app == "CTDC":
            from Commons.apps.ctdc.tsv_source import CtdcTsvSource

            return CtdcTsvSource(tsv_root=tsv_root, tab_row_limit=tab_row_limit)
        if app == "INS":
            from Commons.apps.ins.tsv_source import InsTsvSource

            return InsTsvSource(tsv_root=tsv_root, tab_row_limit=tab_row_limit)
        raise ValueError(
            f"TSV expected data is not configured for app '{app}'. Supported: CTDC, INS."
        )


_LAZY_CTDC: Dict[str, str] = {
    "CtdcTsvSource": "CtdcTsvSource",
    "NODE_INDEX": "NODE_INDEX",
    "NODE_TABLE": "NODE_TABLE",
    "ctdc_node_for_filename": "ctdc_node_for_filename",
    "load_and_merge_versions": "load_and_merge_versions",
    "load_ctdc_merged_frames": "load_ctdc_merged_frames",
}

_LAZY_INS: Dict[str, str] = {
    "InsTsvSource": "InsTsvSource",
    "load_ins_dataset_frames": "load_ins_dataset_frames",
    "load_ins_program_frames": "load_ins_program_frames",
    "read_ins_datasets_page_table": "read_ins_datasets_page_table",
}


def __getattr__(name: str):
    if name in _LAZY_CTDC:
        from Commons.apps.ctdc import tsv_source as mod

        value = getattr(mod, _LAZY_CTDC[name])
        globals()[name] = value
        return value
    if name in _LAZY_INS:
        from Commons.apps.ins import tsv_source as mod

        value = getattr(mod, _LAZY_INS[name])
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AppName",
    "CtdcTsvSource",
    "DATE_FOLDER_FMT",
    "DATE_ZIP_PATTERN",
    "InsTsvSource",
    "NODE_INDEX",
    "NODE_TABLE",
    "TsvSource",
    "TsvSourceBackend",
    "_date_release_folders",
    "_node_for_filename",
    "ctdc_node_for_filename",
    "date_release_folders",
    "frames_to_sqlite",
    "is_date_folder",
    "load_and_merge_versions",
    "load_ctdc_merged_frames",
    "load_ins_dataset_frames",
    "load_ins_program_frames",
    "load_merged_frames",
    "load_tsv_file",
    "merge_all_tsv_versions",
    "merge_row",
    "read_ins_datasets_page_table",
    "tsv_tab_query_label",
]
