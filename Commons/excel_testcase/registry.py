"""Lookup ExcelCaseProfile by app key or Testcases/<APP>/ path."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from Commons.excel_testcase.profile import ExcelCaseProfile

# Populated by Commons.excel_testcase.apps.*
_PROFILES_BY_KEY: Dict[str, ExcelCaseProfile] = {}
_PROFILES_BY_DIR: Dict[str, ExcelCaseProfile] = {}


def register_profile(profile: ExcelCaseProfile) -> None:
    _PROFILES_BY_KEY[profile.app_key.upper()] = profile
    _PROFILES_BY_DIR[profile.testcases_dir] = profile


def _ensure_loaded() -> None:
    if _PROFILES_BY_KEY:
        return
    import Commons.excel_testcase.apps  # noqa: F401 — register GC, CTDC, …


def registered_app_keys() -> List[str]:
    _ensure_loaded()
    return sorted(_PROFILES_BY_KEY.keys())


def get_profile(app_key: str) -> ExcelCaseProfile:
    _ensure_loaded()
    key = app_key.upper()
    if key not in _PROFILES_BY_KEY:
        known = ", ".join(registered_app_keys()) or "(none)"
        raise KeyError(f"No Excel testcase profile for app {app_key!r}. Registered: {known}")
    return _PROFILES_BY_KEY[key]


def get_profile_for_app(app) -> ExcelCaseProfile:
    return get_profile(app.NAME)


def app_key_from_case_path(case_path: Path) -> str:
    _ensure_loaded()
    parts = case_path.parts
    try:
        i = parts.index("Testcases")
        dir_name = parts[i + 1]
    except (ValueError, IndexError) as e:
        raise ValueError(f"Cannot infer app from Excel path: {case_path}") from e
    if dir_name not in _PROFILES_BY_DIR:
        raise ValueError(
            f"No Excel testcase profile for Testcases/{dir_name}/. "
            f"Add Commons/excel_testcase/apps/{dir_name.lower()}.py"
        )
    return _PROFILES_BY_DIR[dir_name].app_key


def fixture_for_case_path(case_path: Path) -> str:
    _ensure_loaded()
    parts = case_path.parts
    i = parts.index("Testcases")
    dir_name = parts[i + 1]
    profile = _PROFILES_BY_DIR.get(dir_name)
    if profile:
        return profile.fixture
    # Apps not yet on Excel cases (INS, C3DC, …) — legacy map for collector wiring
    _LEGACY = {
        "C3DC": "c3dc",
        "ICDC": "icdc",
        "INS": "ins",
        "Bento": "bento",
        "BENTO": "bento",
        "CCDI": "ccdi",
    }
    fix = _LEGACY.get(dir_name) or _LEGACY.get(dir_name.upper())
    if not fix:
        raise ValueError(f"No pytest fixture mapped for Testcases/{dir_name}/ ({case_path})")
    return fix


def profile_for_case_path(case_path: Path) -> Optional[ExcelCaseProfile]:
    _ensure_loaded()
    parts = case_path.parts
    try:
        i = parts.index("Testcases")
        dir_name = parts[i + 1]
    except (ValueError, IndexError):
        return None
    return _PROFILES_BY_DIR.get(dir_name)
