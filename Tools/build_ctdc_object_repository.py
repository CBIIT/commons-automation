#!/usr/bin/env python3
"""Build ObjectRepository/CTDC from Katalon Commons_Automation + crdc-ctdc-ui facet labels."""
from __future__ import annotations

import re
import shutil
import sys
from collections import OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Tools.convert_object_repository import convert_app, read_locator  # noqa: E402

KATALON = ROOT.parent / "Commons_Automation"
OUT = ROOT / "ObjectRepository" / "CTDC"

CHKBX_SUFFIX = re.compile(r"[-_]Chkbx$")
DDN_SUFFIX = re.compile(r"[-_]Ddn$")

# Sidebar section accordions (crdc-ctdc-ui-main/src/bento/dashTemplate.js)
FACET_SECTION = {
    "participants": '(//*[contains(normalize-space(.), "Filter by Participants")])[1]',
    "biospecimens": '(//*[contains(normalize-space(.), "Filter by Biospecimens")])[1]',
    "files": '(//*[contains(normalize-space(.), "Filter by Data Files")])[1]',
}

# Katalon folder -> (yaml page, group key, section, dropdown xpath aligned to UI @id)
FILTER_ORDER = [
    ("participants", "Filters/Diagnosis", "Participants/Diagnosis", "//*[@id='Diagnosis' and @role='button']"),
    ("participants", "Filters/Sex", "Participants/Sex", "(//*[@id='Sex'])[1]"),
    ("participants", "Filters/Race", "Participants/Race", "//*[@id='Race' and @role='button']"),
    ("participants", "Filters/Ethnicity", "Participants/Ethnicity", "//*[@id='Ethnicity' and @role='button']"),
    (
        "participants",
        "Filters/CarcinExposure",
        "Participants/CarcinogenExposure",
        "//*[@id='Carcinogen Exposure' and @role='button']",
    ),
    (
        "participants",
        "Filters/TargetedTherapy",
        "Participants/TargetedTherapy",
        "(//*[@id='Trial Arm'])[1]",
    ),
    (
        "biospecimens",
        "Filters/AnatoCollecSite",
        "Biospecimens/AnatomicalCollectionSite",
        "//*[@id='Anatomical Collection Site' and @role='button']",
    ),
    (
        "biospecimens",
        "Filters/TissueCategory",
        "Biospecimens/TissueCategory",
        "//*[@id='Tissue Category' and @role='button']",
    ),
    (
        "biospecimens",
        "Filters/ColTimepoint",
        "Biospecimens/CollectionTimepoint",
        "//*[@id='Collection Timepoint' and @role='button']",
    ),
    ("files", "Filters/FileType", "Files/FileType", "//*[@id='File Type' and @role='button']"),
    ("files", "Filters/FileFormat", "Files/FileFormat", "//*[@id='File Format' and @role='button']"),
]

RESULT_TAB_OVERRIDES = {
    "Participants-Tab": "//button[@role='tab' and contains(., 'Participants')]",
    "Biospecimens-Tab": "//button[@role='tab' and contains(., 'Biospecimens')]",
    "Files-Tab": "//button[@role='tab' and contains(., 'Files')]",
    "All_Tabs_Next-Btn": "(//button[@type='button' and @aria-label='Next page'])[1]",
}

STATBAR_ORDER = [
    "Studies-Count",
    "Participants-Count",
    "Diagnoses-Count",
    "TargetedTherapies-Count",
    "Biospecimens-Count",
    "Files-Count",
]


def _normalize_xpath(xp: str) -> str:
    xp = xp.strip()
    xp = re.sub(r"@id\s*=\s*", "@id=", xp)
    xp = re.sub(r"\s+", " ", xp)
    return xp


def _load_katalon_folder(katalon_ctdc_root: Path, folder_name: str) -> dict[str, str]:
    folder = katalon_ctdc_root / "Filters" / folder_name
    out = {}
    for rs in sorted(folder.glob("*.rs")):
        name, xp = read_locator(rs)
        if xp:
            out[name] = _normalize_xpath(xp)
    return out


def _checkboxes_from_folder(katalon_ctdc_root: Path, folder_name: str) -> OrderedDict[str, str]:
    elems = _load_katalon_folder(katalon_ctdc_root, folder_name)
    chk = OrderedDict()
    for name, xp in sorted(elems.items()):
        if CHKBX_SUFFIX.search(name):
            key = CHKBX_SUFFIX.sub("", name)
            chk[key] = xp
    return chk


def _plain(obj):
    if isinstance(obj, OrderedDict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def _write_yaml(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        fh.write(f"# CTDC object repository ({path.name})\n")
        yaml.safe_dump(_plain(doc), fh, sort_keys=False, allow_unicode=True, width=4096)


def build_filter_yamls(katalon_ctdc: Path) -> None:
    pages: dict[str, OrderedDict] = {
        "participants": OrderedDict(),
        "biospecimens": OrderedDict(),
        "files": OrderedDict(),
    }
    for section, katalon_rel, group_key, dropdown in FILTER_ORDER:
        folder_name = katalon_rel.split("/", 1)[1]
        checkboxes = _checkboxes_from_folder(katalon_ctdc / "Object Repository" / "CTDC", folder_name)
        checkboxes = _apply_checkbox_fixes(folder_name, checkboxes)
        if not checkboxes:
            raise SystemExit(f"No checkboxes in {katalon_rel}")
        pages[section][group_key] = {
            "facet": FACET_SECTION[section],
            "dropdown": dropdown,
            "checkboxes": dict(checkboxes),
        }
    _write_yaml(OUT / "filters" / "participants.yaml", {"page": "Filters/Participants", "groups": pages["participants"]})
    _write_yaml(OUT / "filters" / "biospecimens.yaml", {"page": "Filters/Biospecimens", "groups": pages["biospecimens"]})
    _write_yaml(OUT / "filters" / "files.yaml", {"page": "Filters/Files", "groups": pages["files"]})


def patch_result_tabs() -> None:
    path = OUT / "result_tabs.yaml"
    if not path.is_file():
        return
    doc = yaml.safe_load(path.read_text()) or {}
    elements = doc.get("elements") or {}
    for key, xp in RESULT_TAB_OVERRIDES.items():
        if key in elements:
            elements[key] = xp
    doc["elements"] = dict(sorted(elements.items()))
    _write_yaml(path, doc)


def patch_statbar() -> None:
    path = OUT / "statbar.yaml"
    if not path.is_file():
        return
    doc = yaml.safe_load(path.read_text()) or {}
    elements = doc.get("elements") or {}
    ordered = OrderedDict()
    for i, key in enumerate(STATBAR_ORDER, start=1):
        if key in elements:
            ordered[key] = f'//*[@id="statsbar_count_{i}"]'
        else:
            ordered[key] = f'//*[@id="statsbar_count_{i}"]'
    doc["elements"] = dict(ordered)
    _write_yaml(path, doc)


def remove_legacy_filter_yamls() -> None:
    legacy = OUT / "filters.yaml"
    if legacy.is_file():
        legacy.unlink()
    filt = OUT / "filters"
    if not filt.is_dir():
        return
    keep = {"participants.yaml", "biospecimens.yaml", "files.yaml"}
    for f in filt.glob("*.yaml"):
        if f.name not in keep:
            f.unlink()


# Katalon objects that used label text instead of checkbox @id — align with Bento facet UI.
CHECKBOX_XPATH_FIXES = {
    ("Diagnosis", "Prostate"): "//*[@id='checkbox_Diagnosis_Prostate cancer, NOS']",
    ("Diagnosis", "Leiomyosarcoma"): "//*[@id='checkbox_Diagnosis_Leiomyosarcoma of the uterus']",
    ("Diagnosis", "SerousEndoAdeno"): "//*[@id='checkbox_Diagnosis_Serous endometrial adenocarcinoma']",
}


def _apply_checkbox_fixes(folder_name: str, checkboxes: OrderedDict[str, str]) -> OrderedDict[str, str]:
    for key, xp in CHECKBOX_XPATH_FIXES.items():
        if key[0] == folder_name and key[1] in checkboxes:
            checkboxes[key[1]] = xp
    return checkboxes


def main() -> int:
    if not KATALON.is_dir():
        raise SystemExit(f"Katalon project not found: {KATALON}")
    if OUT.exists():
        shutil.rmtree(OUT)
    convert_app(KATALON, "CTDC", OUT.parent)
    remove_legacy_filter_yamls()
    build_filter_yamls(KATALON)
    patch_result_tabs()
    patch_statbar()
    from Commons.object_repository import ObjectRepository

    repo = ObjectRepository("CTDC")
    print(f"CTDC: {len(repo._elements)} elements, {len(repo._groups)} filter groups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
