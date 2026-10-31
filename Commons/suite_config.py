"""Suite membership for Excel TC*.xlsx cases (Config/suites.yaml)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import FrozenSet, Optional

import yaml

from Commons.settings import ROOT

SUITES_FILE = ROOT / "Config" / "suites.yaml"

# Must match pytest.ini markers used in suite YAML.
KNOWN_SUITE_MARKERS = frozenset(
    {"smoke", "regression", "quickrun", "sanity", "static", "datarelease"}
)


@lru_cache(maxsize=1)
def load_suite_config() -> dict:
    if not SUITES_FILE.is_file():
        return {}
    data = yaml.safe_load(SUITES_FILE.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{SUITES_FILE.name} must be a YAML mapping (app → suite → patterns)")
    return data


def clear_suite_config_cache() -> None:
    load_suite_config.cache_clear()


def _app_dir_from_case(case_path: Path) -> tuple[str, str]:
    """Return (app folder under Testcases, relative posix path to TC*.xlsx)."""
    parts = case_path.parts
    idx = parts.index("Testcases")
    app_dir = parts[idx + 1]
    rel = PurePosixPath(*parts[idx + 2:])
    return app_dir, rel.as_posix()


def app_has_suite_yaml(app_dir: str) -> bool:
    cfg = load_suite_config()
    block = cfg.get(app_dir)
    return isinstance(block, dict) and bool(block)


def suite_markers_for_excel_case(case_path: Path) -> Optional[FrozenSet[str]]:
    """
    Return suite markers for this Excel case if the app is listed in suites.yaml.

    Returns None if the app is not configured (caller applies legacy TC01/smoke rules).
    """
    app_dir, rel_posix = _app_dir_from_case(case_path)
    cfg = load_suite_config()
    block = cfg.get(app_dir)
    if not isinstance(block, dict):
        return None

    rel_path = PurePosixPath(rel_posix)
    markers: set[str] = set()
    for suite_name, patterns in block.items():
        if suite_name.startswith("_") or not isinstance(patterns, list):
            continue
        if suite_name not in KNOWN_SUITE_MARKERS:
            continue
        for pattern in patterns:
            pat = str(pattern).strip()
            if not pat:
                continue
            if rel_path.match(pat):
                markers.add(suite_name)
                break
    return frozenset(markers)
