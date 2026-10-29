"""
Expected tab/stat data from dated TSV snapshots (Katalon Utils.py pattern).

Used when `expected_source: tsv` in Config/environments.yaml:
  - CTDC — node files under InputFiles/CTDC/<STUDY>/YYYY-MM-DD/
  - INS  — InputFiles/INS/YYYY-MM-DD/*.tsv or bundles like Program.zip (auto-extracted)

Shared pipeline: find release folders → load TSVs → merge by id (newer wins) → in-memory SQLite → SQL from TC*.xlsx.
"""
from __future__ import annotations

import re
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import pandas as pd

from Commons import action_log
from Commons.db_source import ExpectedDataSource, Table, format_db_cell
from Commons.query_reader import QueryFile
from Commons.settings import ROOT
from Commons.tab_setting import apply_tab_row_limit

AppName = str  # "CTDC" | "INS"

# ---------------------------------------------------------------------------
# CTDC node files
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# INS node files
# ---------------------------------------------------------------------------

INS_NODE_INDEX: Dict[str, str] = {
    "program": "program_id",
    "project": "project_id",
    "grant": "grant_id",
    "publication": "pmid",
}

INS_NODE_TABLE: Dict[str, str] = {
    "program": "df_program",
    "project": "df_project",
    "grant": "df_grant",
    "publication": "df_publication",
}

_DATE_FOLDER = "%Y-%m-%d"
_DATE_ZIP = re.compile(r"^\d{4}-\d{2}-\d{2}\.zip$", re.I)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


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


def _is_date_folder(name: str) -> bool:
    try:
        datetime.strptime(name, _DATE_FOLDER)
        return True
    except ValueError:
        return False


def _date_release_folders(tsv_root: Path) -> List[Path]:
    """YYYY-MM-DD dirs: tsv/STUDY/2025-10-23 or tsv/2025-10-23, oldest → newest."""
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


def _node_for_filename(file_name: str) -> Optional[str]:
    """CTDC: match node token in filename (longest token wins)."""
    stem = Path(file_name).stem.lower()
    for node in sorted(NODE_INDEX, key=len, reverse=True):
        if re.search(rf"(^|_|-){re.escape(node)}(_|-|$)", stem):
            return node
    return None


def _ins_node_for_filename(file_name: str) -> Optional[str]:
    """INS: simple substring match on program, project, grant, publication."""
    stem = Path(file_name).stem.lower()
    for node in sorted(INS_NODE_INDEX, key=len, reverse=True):
        if node in stem:
            return node
    return None


def _zip_member_target(tsv_root: Path, zip_path: Path, member: str) -> Optional[Path]:
    """
    Where to write one .tsv from a zip under tsv_root.

    Handles Program.zip (2024-10-29/grant.tsv), YYYY-MM-DD.zip (flat *.tsv), and
    nested bundles (DataSetsTab/2025-05-18/*.tsv).
    """
    if member.startswith("__MACOSX") or member.endswith("/"):
        return None
    parts = Path(member).parts
    if not parts or not parts[-1].lower().endswith(".tsv"):
        return None
    file_name = parts[-1]
    for part in parts[:-1]:
        if _is_date_folder(part):
            return tsv_root / part / file_name
    if _DATE_ZIP.match(zip_path.name):
        return tsv_root / zip_path.stem / file_name
    if len(parts) >= 2:
        return tsv_root.joinpath(*parts)
    return None


def _ensure_ins_zips_extracted(tsv_root: Path) -> None:
    """INS: extract missing .tsv from any *.zip in InputFiles/INS (Program.zip, etc.)."""
    for zip_path in sorted(tsv_root.glob("*.zip")):
        if not zip_path.is_file():
            continue
        wrote = False
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                target = _zip_member_target(tsv_root, zip_path, member)
                if target is None or target.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))
                wrote = True
        if wrote:
            action_log.say(f"INS TSV extracted from {zip_path.name}")


def _release_label(version_path: Path, tsv_root: Path) -> str:
    if version_path == tsv_root:
        return version_path.name
    return f"{version_path.parent.name}/{version_path.name}"


def _merge_row(current: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    """Katalon-style merge: same index updates in place, then append new ids."""
    if current.empty:
        return df_new
    overlap = df_new.index.intersection(current.index)
    for idx in overlap:
        if not df_new.loc[idx].equals(current.loc[idx]):
            current.loc[idx] = df_new.loc[idx]
    df_new = df_new[~df_new.index.isin(current.index)]
    return pd.concat([current, df_new])


def _merge_releases(
    tsv_root: Path,
    versions: List[Path],
    node_index: Dict[str, str],
    node_for_filename: Callable[[str], Optional[str]],
    log_loaded: Callable[[str], None],
) -> Dict[str, pd.DataFrame]:
    """Walk each release folder and merge all node TSVs into one frame per node."""
    frames: Dict[str, pd.DataFrame] = {node: pd.DataFrame() for node in node_index}
    for version_path in versions:
        for file_path in version_path.iterdir():
            if file_path.suffix.lower() not in (".tsv", ".txt"):
                continue
            node = node_for_filename(file_path.name)
            if node is None:
                continue
            df_new = load_tsv_file(file_path, node_index[node])
            if df_new is None:
                continue
            frames[node] = _merge_row(frames[node], df_new)
        log_loaded(_release_label(version_path, tsv_root))
    return frames


def _frames_to_sqlite(
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


# ---------------------------------------------------------------------------
# Per-app load rules (only the parts that differ)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _TsvAppConfig:
    default_root: str
    node_index: Dict[str, str]
    node_table: Dict[str, str]
    node_for_filename: Callable[[str], Optional[str]]
    prepare_root: Callable[[Path], None]
    release_folders: Callable[[Path], List[Path]]
    validate: Callable[[Dict[str, pd.DataFrame], Path], None]
    loaded_log: Callable[[str], None]


def _ctdc_prepare(_root: Path) -> None:
    return None


def _ctdc_release_folders(tsv_root: Path) -> List[Path]:
    versions = _date_release_folders(tsv_root)
    if not versions:
        raise RuntimeError(
            f"No YYYY-MM-DD folders under {tsv_root}. "
            "Add InputFiles/CTDC/CMB/2025-10-23/ (and other studies the same way)."
        )
    return versions


def _ctdc_validate(_frames: Dict[str, pd.DataFrame], _root: Path) -> None:
    return None


def _ctdc_loaded_log(version: str) -> None:
    action_log.say(f"Data successfully loaded for release: {version}")


def _ins_prepare(tsv_root: Path) -> None:
    _ensure_ins_zips_extracted(tsv_root)


def _ins_release_folders(tsv_root: Path) -> List[Path]:
    versions = _date_release_folders(tsv_root)
    return versions if versions else [tsv_root]


def _ins_validate(frames: Dict[str, pd.DataFrame], tsv_root: Path) -> None:
    if all(frames[node].empty for node in INS_NODE_INDEX):
        raise RuntimeError(
            f"No INS TSV node files loaded under {tsv_root}. "
            "Expected InputFiles/INS/YYYY-MM-DD/*.tsv or Program.zip (auto-extracted)."
        )
    if "cancer_type" not in frames["program"].columns:
        raise RuntimeError(
            f"INS program TSV missing cancer_type column (loaded columns: {list(frames['program'].columns)}). "
            "Re-extract Program.zip or refresh program.tsv from ins-data."
        )


def _ins_loaded_log(version: str) -> None:
    action_log.say(f"INS TSV loaded for release: {version}")


_TSV_APPS: Dict[AppName, _TsvAppConfig] = {
    "CTDC": _TsvAppConfig(
        default_root="InputFiles/CTDC",
        node_index=NODE_INDEX,
        node_table=NODE_TABLE,
        node_for_filename=_node_for_filename,
        prepare_root=_ctdc_prepare,
        release_folders=_ctdc_release_folders,
        validate=_ctdc_validate,
        loaded_log=_ctdc_loaded_log,
    ),
    "INS": _TsvAppConfig(
        default_root="InputFiles/INS",
        node_index=INS_NODE_INDEX,
        node_table=INS_NODE_TABLE,
        node_for_filename=_ins_node_for_filename,
        prepare_root=_ins_prepare,
        release_folders=_ins_release_folders,
        validate=_ins_validate,
        loaded_log=_ins_loaded_log,
    ),
}


def _resolve_tsv_root(tsv_root: str, app: AppName) -> Path:
    cfg = _TSV_APPS[app]
    root = Path(tsv_root) if tsv_root else ROOT / cfg.default_root
    if not root.is_absolute():
        root = ROOT / root
    return root


def load_merged_frames(tsv_root: Path, app: AppName) -> Dict[str, pd.DataFrame]:
    """Load and merge all releases for CTDC or INS."""
    if app not in _TSV_APPS:
        raise ValueError(f"TSV expected data is not configured for app '{app}' (use CTDC or INS).")
    cfg = _TSV_APPS[app]
    if not tsv_root.is_dir():
        if app == "INS":
            raise RuntimeError(
                f"INS TSV folder not found: {tsv_root}. "
                "Copy InputFiles/INS/<date>/ or add Program.zip beside TC*.xlsx."
            )
        raise RuntimeError(
            f"CTDC TSV folder not found: {tsv_root}. "
            "Use InputFiles/CTDC/<STUDY>/YYYY-MM-DD/ or set CTDC_TSV_ROOT."
        )
    cfg.prepare_root(tsv_root)
    versions = cfg.release_folders(tsv_root)
    frames = _merge_releases(tsv_root, versions, cfg.node_index, cfg.node_for_filename, cfg.loaded_log)
    cfg.validate(frames, tsv_root)
    return frames


def load_and_merge_versions(tsv_root: Path) -> Dict[str, pd.DataFrame]:
    """CTDC entry point (kept for tests and direct callers)."""
    return load_merged_frames(tsv_root, "CTDC")


# ---------------------------------------------------------------------------
# Expected data source (CTDC + INS)
# ---------------------------------------------------------------------------


class TsvSource(ExpectedDataSource):
    """Run TabQuery / StatQuery SQL from Excel against merged TSV snapshots."""

    def __init__(
        self,
        tsv_root: str = "",
        app: AppName = "CTDC",
        tab_row_limit: Optional[int] = None,
    ):
        if app not in _TSV_APPS:
            raise ValueError(f"Unknown TSV app '{app}'. Supported: {list(_TSV_APPS)}.")
        self._app = app
        self._cfg = _TSV_APPS[app]
        self._tsv_root = _resolve_tsv_root(tsv_root, app)
        self._tab_row_limit = tab_row_limit
        self._conn: Optional[sqlite3.Connection] = None
        self._logged_load = False

    def _ensure_loaded(self) -> sqlite3.Connection:
        if self._conn is None:
            frames = load_merged_frames(self._tsv_root, self._app)
            self._conn = _frames_to_sqlite(frames, self._cfg.node_index, self._cfg.node_table)
            if not self._logged_load:
                action_log.say(f"{self._app} TSV expected data loaded from {self._tsv_root}")
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

    def close_connection(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def close(self) -> None:
        self.close_connection()
