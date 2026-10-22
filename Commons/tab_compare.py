"""
Per-app result tab settings from Config/tab_compare.yaml.

  - tab_row_limit / pagination_max_pages — UI scrape + DB tab Cypher LIMIT
  - tabs — enable or skip verify_tab (UI read + DB query) per tab name
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

import yaml

from Commons.settings import ROOT

CONFIG_FILE = ROOT / "Config" / "tab_compare.yaml"
# Legacy filename (row limits only); used if tab_compare.yaml is missing.
_LEGACY_FILE = ROOT / "Config" / "query_limits.yaml"


@dataclass(frozen=True)
class TabCompareSettings:
    """Row limits and per-tab on/off for one app."""

    tab_row_limit: int
    pagination_max_pages: int
    tab_execution: Dict[str, bool] = field(default_factory=dict)


def load_tab_compare_config() -> dict:
    path = CONFIG_FILE if CONFIG_FILE.is_file() else _LEGACY_FILE
    if not path.is_file():
        return {}
    with open(path) as fh:
        return yaml.safe_load(fh) or {}


def _int_from_env(keys: tuple[str, ...]) -> Optional[int]:
    for key in keys:
        raw = os.environ.get(key)
        if raw is not None and str(raw).strip():
            try:
                return int(str(raw).strip())
            except ValueError:
                continue
    return None


def _normalize_tab_execution(raw: object) -> Dict[str, bool]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, bool] = {}
    for key, val in raw.items():
        if key is None:
            continue
        out[str(key).strip()] = bool(val)
    return out


def settings_for_app(app: str, cfg: dict | None = None) -> TabCompareSettings:
    """YAML defaults, per-app block, env overrides for row limits."""
    cfg = cfg or load_tab_compare_config()
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

    return TabCompareSettings(
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
    True if this tab should run verify_tab.

    `tab_name` is the TABS key (after C3DC TAB_VERIFY_ALIASES). YAML may use test
    labels (e.g. Treatments) or canonical keys (Treatment); omitted tabs default on.
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
    """Replace trailing LIMIT on tab Cypher (not used for stat bar queries)."""
    if limit is None or limit <= 0:
        return cypher
    text = cypher.strip().rstrip(";").strip()
    text = re.sub(r"\s+LIMIT\s+\d+\s*$", "", text, flags=re.IGNORECASE)
    return f"{text}\nLIMIT {int(limit)}"


# Backward-compatible names
limits_for_app = settings_for_app
load_query_limits_config = load_tab_compare_config
