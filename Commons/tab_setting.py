"""
Loads result-tab behavior from Config/tab_setting.yaml.

Controls how many table rows we compare (UI vs database) and which result tabs
run during a test. Stat bar counts are always checked; this file does not gate them.

YAML keys (see Config/tab_setting.yaml for per-app examples):

  tab_row_limit          — max rows read from the UI and returned from DB query
  pagination_max_pages   — safety cap on "Next page" clicks in the browser
  tabs.<name>: true      — run this tab (read UI + run DB query + compare)
  tabs.<name>: false     — skip this tab (test continues; tab marked SKIPPED)

Shell overrides (row / page caps only; tabs stay in YAML):

  TAB_ROW_LIMIT, TAB_ROW_LIMIT_<APP>
  PAGINATION_MAX_PAGES, PAGINATION_MAX_PAGES_<APP>

Used by settings.get_app_settings, db_source (Cypher LIMIT), table_reader (UI scrape),
and BaseApp.verify_tab (skip disabled tabs).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Optional

import yaml

from Commons.settings import ROOT

# ---------------------------------------------------------------------------
# Config file paths
# ---------------------------------------------------------------------------

CONFIG_FILE = ROOT / "Config" / "tab_setting.yaml"
# Older repo clones; only used when tab_setting.yaml is missing.
_LEGACY_FILES = (
    ROOT / "Config" / "tab_compare.yaml",
    ROOT / "Config" / "query_limits.yaml",
)


# ---------------------------------------------------------------------------
# Resolved settings for one app (C3DC, GC, ICDC, CTDC)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TabSettingSettings:
    """Row limits and per-tab on/off after YAML + env merge."""

    tab_row_limit: int  # UI rows + DB tab Cypher LIMIT (not stat bar)
    pagination_max_pages: int  # max "Next page" clicks when scraping UI tables
    tab_execution: Dict[str, bool] = field(
        default_factory=dict
    )  # portal tab label -> run verify_tab or skip


# ---------------------------------------------------------------------------
# Load YAML
# ---------------------------------------------------------------------------


def _config_path() -> Path | None:
    if CONFIG_FILE.is_file():
        return CONFIG_FILE
    for path in _LEGACY_FILES:
        if path.is_file():
            return path
    return None


def load_tab_setting_config() -> dict:
    """Raw parsed YAML, or {} if no config file exists."""
    path = _config_path()
    if path is None:
        return {}
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _int_from_env(keys: tuple[str, ...]) -> Optional[int]:
    """First positive integer from the given env var names, or None."""
    for key in keys:
        raw = os.environ.get(key)
        if raw is not None and str(raw).strip():
            try:
                return int(str(raw).strip())
            except ValueError:
                continue
    return None


def _normalize_tab_execution(raw: object) -> Dict[str, bool]:
    """Parse apps.<APP>.tabs from YAML into a label -> bool map."""
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, bool] = {}
    for key, val in raw.items():
        if key is None:
            continue
        out[str(key).strip()] = bool(val)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def settings_for_app(app: str, cfg: dict | None = None) -> TabSettingSettings:
    """
    Defaults from YAML root, per-app block under apps.<APP>, then env overrides.

    Env wins only for tab_row_limit and pagination_max_pages (not per-tab toggles).
    """
    cfg = cfg or load_tab_setting_config()
    app_block = (cfg.get("apps") or {}).get(app) or {}

    row_default = int(cfg.get("default_tab_row_limit") or 100)
    pages_default = int(cfg.get("default_pagination_max_pages") or 50)

    tab_row_limit = int(app_block.get("tab_row_limit", row_default))
    pagination_max_pages = int(app_block.get("pagination_max_pages", pages_default))
    tab_execution = _normalize_tab_execution(app_block.get("tabs"))

    app_u = app.upper()
    row_env = _int_from_env((f"TAB_ROW_LIMIT_{app_u}", "TAB_ROW_LIMIT"))
    if row_env is not None and row_env > 0:
        tab_row_limit = row_env

    pages_env = _int_from_env((f"PAGINATION_MAX_PAGES_{app_u}", "PAGINATION_MAX_PAGES"))
    if pages_env is not None and pages_env > 0:
        pagination_max_pages = pages_env

    return TabSettingSettings(
        tab_row_limit=tab_row_limit,
        pagination_max_pages=pagination_max_pages,
        tab_execution=tab_execution,
    )


def tab_is_enabled(
    tab_execution: Mapping[str, bool],
    tab_name: str,
    verify_aliases: Mapping[str, str] | None = None,
) -> bool:
    """
    Whether verify_tab should run for this tab (UI read + DB query + compare).

    tab_name is the internal TABS key (after C3DC TAB_VERIFY_ALIASES). YAML may
    use portal labels (e.g. Treatments) or keys (Treatment). Tabs omitted from
    tabs: in YAML default to enabled (True).
    """
    if not tab_execution:
        return True
    names_to_check = [tab_name]
    for label, canonical in (verify_aliases or {}).items():
        if canonical == tab_name:
            names_to_check.append(label)
    for name in names_to_check:
        if name in tab_execution:
            return bool(tab_execution[name])
    return True


def apply_tab_row_limit(cypher: str, limit: Optional[int]) -> str:
    """
    Replace a trailing LIMIT on tab Cypher so DB row count matches tab_row_limit.

    Not used for stat bar queries—only tab table fetch in db_source.
    """
    if limit is None or limit <= 0:
        return cypher
    text = cypher.strip().rstrip(";").strip()
    text = re.sub(r"\s+LIMIT\s+\d+\s*$", "", text, flags=re.IGNORECASE)
    return f"{text}\nLIMIT {int(limit)}"


# ---------------------------------------------------------------------------
# Backward-compatible names (older imports / filenames)
# ---------------------------------------------------------------------------

TabCompareSettings = TabSettingSettings
limits_for_app = settings_for_app
load_tab_compare_config = load_tab_setting_config
load_query_limits_config = load_tab_setting_config
