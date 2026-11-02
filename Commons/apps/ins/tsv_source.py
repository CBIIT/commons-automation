"""INS expected data: Programs TSVs, DataSetsTab.zip, and Datasets Explore UI scrape."""
from __future__ import annotations

import sqlite3
import time
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

import pandas as pd

from Commons import action_log
from Commons.db_source import Table, format_db_cell
from Commons.query_reader import QueryFile
from Commons.settings import ROOT
from Commons.tab_setting import apply_tab_row_limit
from Commons.tsv_source import (
    DATE_ZIP_PATTERN,
    TsvSourceBackend,
    date_release_folders,
    frames_to_sqlite,
    is_date_folder,
    merge_all_tsv_versions,
    tsv_tab_query_label,
)

if TYPE_CHECKING:
    from Commons.browser_actions import Ui
    from Commons.object_repository import ObjectRepository

INS_DEFAULT_TSV_ROOT = "InputFiles/INS"

# ---------------------------------------------------------------------------
# INS Programs node files
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

# ---------------------------------------------------------------------------
# INS DataSets node files (DataSetsTab.zip)
# ---------------------------------------------------------------------------

INS_DATASET_INDEX: Dict[str, str] = {
    "cedcd_datasets": "dataset_source_id",
    "dbgap_datasets": "dataset_source_id",
    "geo_datasets": "dataset_source_id",
}

INS_DATASET_TABLE: Dict[str, str] = {
    "cedcd_datasets": "df_cedcd",
    "dbgap_datasets": "df_dbgap",
    "geo_datasets": "df_geo",
}

INS_DATASETS_UI_HEADER: tuple[str, ...] = (
    "Title",
    "Source ID",
    "Primary Disease",
    "Sample Count",
)


def ins_program_node_for_filename(file_name: str) -> Optional[str]:
    """Match program / project / grant / publication TSV filenames."""
    stem = Path(file_name).stem.lower()
    for node in sorted(INS_NODE_INDEX, key=len, reverse=True):
        if node in stem:
            return node
    return None


def ins_dataset_node_for_filename(file_name: str) -> Optional[str]:
    """Match cedcd_datasets / dbgap_datasets / geo_datasets TSV filenames."""
    stem = Path(file_name).stem.lower()
    for node in sorted(INS_DATASET_INDEX, key=len, reverse=True):
        if node in stem:
            return node
    return None


def ins_dataset_release_folders(tsv_root: Path) -> List[Path]:
    """Dated folders under DataSetsTab/ (from DataSetsTab.zip)."""
    bundle = tsv_root / "DataSetsTab"
    if not bundle.is_dir():
        return []
    versions = date_release_folders(bundle)
    if versions:
        return versions
    if any(bundle.glob("*.tsv")):
        return [bundle]
    return []


def _zip_member_target(tsv_root: Path, zip_path: Path, member: str) -> Optional[Path]:
    if member.startswith("__MACOSX") or member.endswith("/"):
        return None
    parts = Path(member).parts
    if not parts or not parts[-1].lower().endswith(".tsv"):
        return None
    file_name = parts[-1]
    for part in parts[:-1]:
        if is_date_folder(part):
            return tsv_root / part / file_name
    if DATE_ZIP_PATTERN.match(zip_path.name):
        return tsv_root / zip_path.stem / file_name
    if len(parts) >= 2:
        return tsv_root.joinpath(*parts)
    return None


def ensure_ins_zips_extracted(tsv_root: Path) -> None:
    """Extract missing .tsv from Programs.zip, DataSetsTab.zip, etc."""
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


def _ins_programs_loaded_log(version: str) -> None:
    action_log.say(f"INS Programs TSV loaded for release: {version}")


def _ins_datasets_loaded_log(version: str) -> None:
    action_log.say(f"INS DataSets TSV loaded for release: {version}")


def ins_program_bundle_folders(tsv_root: Path) -> List[Path]:
    """Top-level dirs (not YYYY-MM-DD) that contain Programs node TSVs."""
    bundles: List[Path] = []
    for child in tsv_root.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if is_date_folder(child.name):
            continue
        for file_path in child.iterdir():
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in (".tsv", ".txt"):
                continue
            if ins_program_node_for_filename(file_path.name) is not None:
                bundles.append(child)
                break
    bundles.sort(key=lambda path: path.name)
    return bundles


def ins_program_release_folders(tsv_root: Path) -> List[Path]:
    versions = date_release_folders(tsv_root)
    seen = {path.resolve() for path in versions}
    for bundle in ins_program_bundle_folders(tsv_root):
        resolved = bundle.resolve()
        if resolved not in seen:
            versions.append(bundle)
            seen.add(resolved)
    return versions if versions else [tsv_root]


def _validate_ins_program_frames(frames: Dict[str, pd.DataFrame], tsv_root: Path) -> None:
    if all(frames[node].empty for node in INS_NODE_INDEX):
        raise RuntimeError(
            f"No INS Programs TSV loaded under {tsv_root}. "
            "Expected InputFiles/INS/YYYY-MM-DD/*.tsv or Programs.zip (auto-extracted)."
        )
    if "cancer_type" not in frames["program"].columns:
        raise RuntimeError(
            f"INS program TSV missing cancer_type column (loaded columns: {list(frames['program'].columns)}). "
            "Re-extract Programs.zip or refresh program.tsv from ins-data."
        )


def resolve_ins_tsv_root(tsv_root: str) -> Path:
    root = Path(tsv_root) if tsv_root else ROOT / INS_DEFAULT_TSV_ROOT
    if not root.is_absolute():
        root = ROOT / root
    return root


def load_ins_program_frames(tsv_root: Path) -> Dict[str, pd.DataFrame]:
    """Load and merge INS Programs explore TSVs (program, project, grant, publication)."""
    if not tsv_root.is_dir():
        raise RuntimeError(
            f"INS TSV folder not found: {tsv_root}. "
            "Copy InputFiles/INS/<date>/ or add Programs.zip beside TC*.xlsx."
        )
    ensure_ins_zips_extracted(tsv_root)
    versions = ins_program_release_folders(tsv_root)
    frames = merge_all_tsv_versions(
        tsv_root,
        versions,
        INS_NODE_INDEX,
        ins_program_node_for_filename,
        _ins_programs_loaded_log,
    )
    _validate_ins_program_frames(frames, tsv_root)
    return frames


def load_ins_dataset_frames(tsv_root: Path) -> Dict[str, pd.DataFrame]:
    """Load and merge INS DataSets TSVs (cedcd / dbgap / geo)."""
    if not tsv_root.is_dir():
        raise RuntimeError(
            f"INS TSV folder not found: {tsv_root}. Add InputFiles/INS/DataSetsTab.zip."
        )
    ensure_ins_zips_extracted(tsv_root)
    versions = ins_dataset_release_folders(tsv_root)
    if not versions:
        raise RuntimeError(
            f"No INS dataset TSV releases under {tsv_root / 'DataSetsTab'}. "
            "Extract DataSetsTab.zip (YYYY-MM-DD/*.tsv)."
        )
    frames = merge_all_tsv_versions(
        tsv_root,
        versions,
        INS_DATASET_INDEX,
        ins_dataset_node_for_filename,
        _ins_datasets_loaded_log,
    )
    if all(frames[node].empty for node in INS_DATASET_INDEX):
        raise RuntimeError(
            f"No INS dataset TSV files loaded from {tsv_root / 'DataSetsTab'}. "
            "Expected cedcd_datasets.tsv, dbgap_datasets.tsv, geo_datasets.tsv."
        )
    return frames


# ---------------------------------------------------------------------------
# INS DataSets — UI card table
# ---------------------------------------------------------------------------


def _playwright_card_cell_text(card, relative_xpath: str) -> str:
    try:
        loc = card.locator(f"xpath={relative_xpath}")
        if loc.count() == 0:
            return ""
        return (loc.first.inner_text() or "").strip()
    except Exception:
        return ""


def read_ins_datasets_page_table(ui: "Ui", repo: "ObjectRepository") -> Table:
    """Paginated Datasets card grid (Katalon verifyUiAgainstTsvForInsDatasetsTab)."""
    title_rel = ".//a[starts-with(@href, '#/dataset/')]"
    source_rel = (
        ".//a[starts-with(@href, 'https://cedcd') or starts-with(@href, 'https://www.ncbi.nlm')]"
    )
    disease_rel = ".//*[@class='itemSpan']"
    sample_rel = ".//*[@class='textSpan sampleCountHighlight']"

    ui.click(repo.xpath("DataSets/RowsPerPage-Dd"), repo_key="DataSets/RowsPerPage-Dd")
    ui.click(repo.xpath("DataSets/RowPerPaDd-Value"), repo_key="DataSets/RowPerPaDd-Value")
    ui.wait_idle()
    time.sleep(1.5)

    rows: List[List[str]] = []
    next_xp = repo.xpath("DataSets/Next-Btn")
    while True:
        cards = ui.page.locator("xpath=//*[@class='container']")
        count = cards.count()
        action_log.say(f"INS DataSets cards on page: {count}")
        for i in range(count):
            card = cards.nth(i)
            title = _playwright_card_cell_text(card, title_rel)
            if not title:
                continue
            rows.append(
                [
                    title,
                    _playwright_card_cell_text(card, source_rel),
                    _playwright_card_cell_text(card, disease_rel),
                    _playwright_card_cell_text(card, sample_rel),
                ]
            )

        next_btn = ui.page.locator(f"xpath={next_xp}")
        if next_btn.count() == 0:
            break
        cls = next_btn.first.get_attribute("class") or ""
        if "disabled" in cls:
            break
        ui.scroll_into_view(next_xp)
        time.sleep(2)
        ui.click(next_xp, repo_key="DataSets/Next-Btn")
        ui.wait_idle()
        time.sleep(1)

    return Table(header=list(INS_DATASETS_UI_HEADER), rows=rows)


class InsTsvSource(TsvSourceBackend):
    """Run TabQuery / StatQuery SQL from Excel against merged INS TSV snapshots."""

    def __init__(self, tsv_root: str = "", tab_row_limit: Optional[int] = None):
        self._tsv_root = resolve_ins_tsv_root(tsv_root)
        self._tab_row_limit = tab_row_limit
        self._programs_conn: Optional[sqlite3.Connection] = None
        self._datasets_conn: Optional[sqlite3.Connection] = None
        self._logged_programs = False

    def _ensure_programs_sqlite(self) -> sqlite3.Connection:
        if self._programs_conn is None:
            frames = load_ins_program_frames(self._tsv_root)
            self._programs_conn = frames_to_sqlite(frames, INS_NODE_INDEX, INS_NODE_TABLE)
            if not self._logged_programs:
                action_log.say(f"INS Programs TSV expected data loaded from {self._tsv_root}")
                self._logged_programs = True
        return self._programs_conn

    def _ensure_datasets_sqlite(self) -> sqlite3.Connection:
        if self._datasets_conn is None:
            frames = load_ins_dataset_frames(self._tsv_root)
            self._datasets_conn = frames_to_sqlite(
                frames, INS_DATASET_INDEX, INS_DATASET_TABLE
            )
            action_log.say(
                f"INS DataSets TSV expected data loaded from {self._tsv_root / 'DataSetsTab'}"
            )
        return self._datasets_conn

    def run_sql_as_table(self, sql: str, query_label: str = "tab query from tsv") -> Table:
        action_log.memgraph_query(query_label, sql)
        conn = self._ensure_programs_sqlite()
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

    def fetch_ins_datasets_table(self, query_file: QueryFile) -> Table:
        sql = query_file.query_for_tab("DatasetsTab")
        action_log.memgraph_query("INS DataSets tab query from tsv", sql)
        conn = self._ensure_datasets_sqlite()
        cur = conn.execute(sql)
        header = [col[0] for col in cur.description] if cur.description else []
        rows = [[format_db_cell(value) for value in row] for row in cur.fetchall()]
        table = Table(header=header, rows=rows)
        action_log.memgraph_db_table(table.header, table.rows)
        return table

    def close_connection(self) -> None:
        if self._programs_conn is not None:
            self._programs_conn.close()
            self._programs_conn = None
        if self._datasets_conn is not None:
            self._datasets_conn.close()
            self._datasets_conn = None

    def close(self) -> None:
        self.close_connection()
