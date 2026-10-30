"""Extract INS TSV bundles (Programs.zip, DataSetsTab.zip) before loading expected data."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterable, Tuple

from Commons import action_log

# (zip name under InputFiles/INS/, top-level folder inside the archive)
INS_TSV_BUNDLES: Tuple[Tuple[str, str], ...] = (
    ("Programs.zip", "Programs"),
    ("DataSetsTab.zip", "DataSetsTab"),
)

_SKIP_ZIP_PREFIXES = ("__MACOSX/",)
_SKIP_ZIP_SUFFIXES = (".DS_Store",)


def _zip_member_ok(name: str) -> bool:
    if name.endswith("/"):
        return True
    if any(name.startswith(p) for p in _SKIP_ZIP_PREFIXES):
        return False
    if "/__MACOSX/" in name or name.startswith("__MACOSX/"):
        return False
    if name.endswith(_SKIP_ZIP_SUFFIXES) or "/." in name and name.split("/")[-1].startswith("."):
        return False
    return True


def _needs_extract(zip_path: Path, extract_root: Path) -> bool:
    """Re-extract when the bundle folder is missing or the zip is newer than all extracted files."""
    if not extract_root.is_dir():
        return True
    tsv_files = list(extract_root.rglob("*.tsv")) + list(extract_root.rglob("*.txt"))
    if not tsv_files:
        return True
    zip_mtime = zip_path.stat().st_mtime
    newest = max(f.stat().st_mtime for f in tsv_files)
    return zip_mtime > newest


def extract_ins_tsv_bundle(tsv_root: Path, zip_name: str, folder_name: str) -> bool:
    """
    Extract zip into tsv_root when needed. Returns True if extraction ran.
    """
    zip_path = tsv_root / zip_name
    if not zip_path.is_file():
        return False
    extract_root = tsv_root / folder_name
    if not _needs_extract(zip_path, extract_root):
        return False
    action_log.say(f"INS extracting {zip_name} → {extract_root.relative_to(tsv_root)}/")
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if not _zip_member_ok(member):
                continue
            zf.extract(member, tsv_root)
    return True


def ensure_ins_tsv_bundles(tsv_root: Path) -> None:
    """Unpack committed zip bundles under InputFiles/INS/ (idempotent, mtime-aware)."""
    for zip_name, folder_name in INS_TSV_BUNDLES:
        extract_ins_tsv_bundle(tsv_root, zip_name, folder_name)


def ins_tsv_release_paths(tsv_root: Path) -> Iterable[Path]:
    """Folders to scan for INS node TSVs (dated releases, Programs bundle, DataSetsTab)."""
    from Commons.tsv_source import _date_release_folders

    seen: set[Path] = set()
    for path in _date_release_folders(tsv_root):
        if path not in seen:
            seen.add(path)
            yield path
    programs = tsv_root / "Programs"
    if programs.is_dir():
        yield programs
    datasets_root = tsv_root / "DataSetsTab"
    if datasets_root.is_dir():
        dated = _date_release_folders(datasets_root)
        if dated:
            for path in dated:
                if path not in seen:
                    seen.add(path)
                    yield path
        else:
            yield datasets_root
