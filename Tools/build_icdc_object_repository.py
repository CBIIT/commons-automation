#!/usr/bin/env python3
"""Build ObjectRepository/ICDC from Katalon Commons_Automation (Canine) + icdc-fe-be facet labels."""
from __future__ import annotations

import html
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Tools.convert_object_repository import convert_app  # noqa: E402

KATALON = ROOT.parent / "Commons_Automation"
ICDC_FE = ROOT.parent / "icdc-fe-be" / "bento-icdc-frontend-development"
OUT = ROOT / "ObjectRepository" / "ICDC"

CHKBX_SUFFIX = re.compile(r"[-_]Chkbx$|[-_]Chbx$")
DDN_SUFFIX = re.compile(r"[-_]Ddn$")
CHECKBOX_ID_ATTR_RE = re.compile(r"@id=['\"](checkbox_[^'\"]+)['\"]")

FACET_SECTION = {
    "cases": "(//*[contains(normalize-space(.), 'Filter By Cases')])[1]",
    "samples": "(//*[contains(normalize-space(.), 'Filter By Samples')])[1]",
    "files": "(//*[contains(normalize-space(.), 'Filter By Files')])[1]",
}

# section, katalon folder under Filter/, group key, UI accordion @id label
FILTER_ORDER = [
    ("cases", None, "Cases/Program", "Program"),
    ("cases", "Study", "Cases/Study", "Study"),
    ("cases", "StudyType", "Cases/StudyType", "Study Type"),
    ("cases", "Biobank", "Cases/Biobank", "Biobank"),
    ("cases", "StudyParticipation", "Cases/StudyParticipation", "Study Participation"),
    ("cases", "Breed", "Cases/Breed", "Breed"),
    ("cases", "Diagnosis", "Cases/Diagnosis", "Diagnosis"),
    ("cases", "PrimDiseaseSite", "Cases/PrimaryDiseaseSite", "Primary Disease Site"),
    ("cases", "StageOfDisease", "Cases/StageOfDisease", "Stage of Disease"),
    ("cases", "ResponseToTreatment", "Cases/ResponseToTreatment", "Response to Treatment"),
    ("cases", "Sex", "Cases/Sex", "Sex"),
    ("cases", "NeuteredStatus", "Cases/NeuteredStatus", "Neutered Status"),
    ("samples", "SampleSite", "Samples/SampleSite", "Sample Site"),
    ("samples", "SampleType", "Samples/SampleType", "Sample Type"),
    ("samples", "SamplePathology", "Samples/SamplePathology", "Sample Pathology"),
    ("files", "FileAssociation", "Files/FileAssociation", "File Association"),
    ("files", "FileType", "Files/FileType", "File Type"),
    ("files", "FileFormat", "Files/FileFormat", "File Format"),
]

PROGRAM_CHECKBOXES = OrderedDict(
    [
        ("PCCR", "//*[@id='checkbox_Program_PCCR']"),
        ("COP", "//*[@id='checkbox_Program_COP']"),
        ("CMCP", "//*[@id='checkbox_Program_CMCP']"),
    ]
)

# Katalon short keys → Bento checkbox value suffix (Stage of Disease)
STAGE_VALUE_BY_KEY = {
    "2": "II",
    "2b": "IIb",
    "2a": "IIa",
    "3": "III",
    "3a": "IIIa",
    "3b": "IIIb",
    "4": "IV",
    "4a": "IVa",
    "4b": "IVb",
    "5": "V",
    "5a": "Va",
    "5b": "Vb",
    "Ia": "Ia",
}

STUDY_TYPE_VALUE_BY_KEY = {
    "Canine_Filter_StudyType-ClinTrials": "Clinical Trial",
    "Canine_Filter_StudyType-Transcrip": "Transcriptomics",
}

STATBAR_ORDER = [
    "Canine_StatBar-DataVolume",
    "Canine_StatBar-Programs",
    "Canine_StatBar-Studies",
    "Canine_StatBar-Cases",
    "Canine_StatBar-Samples",
    "Canine_StatBar-CaseFiles",
    "Canine_StatBar-StudyFiles",
]

RESULT_TAB_OVERRIDES = {
    "CanineResults_Cases_Tab": "//button[@role='tab' and contains(., 'Cases')]",
    "CanineResults_Samples_Tab": "//button[@role='tab' and contains(., 'Samples')]",
    "CanineResults_CaseFiles_Tab": "//button[@role='tab' and contains(., 'Case Files')]",
    "CanineResults_StudyFiles_Tab": "//button[@role='tab' and contains(., 'Study Files')]",
    "Canine_CasesTabNextBtn": "(//button[@type='button' and @aria-label='Next page'])[1]",
    "Canine_SamplesTabNextBtn": "(//button[@type='button' and @aria-label='Next page'])[1]",
}


def _normalize_xpath(xp: str) -> str:
    xp = xp.strip()
    xp = re.sub(r"@id\s*=\s*", "@id=", xp)
    xp = re.sub(r"\s+", " ", xp)
    return xp


def _checkbox_id_from_rs(rs_file: Path) -> str | None:
    raw = html.unescape(rs_file.read_text(encoding="utf-8", errors="replace"))
    ids = CHECKBOX_ID_ATTR_RE.findall(raw)
    ids = [i for i in ids if i.startswith("checkbox_")]
    if not ids:
        return None
    return max(ids, key=len)


def read_checkbox_locator(
    rs_file: Path, *, folder_name: str, ui_label: str
) -> tuple[str, str | None]:
    root = ET.parse(rs_file).getroot()
    name = root.findtext("name") or rs_file.stem
    cid = _checkbox_id_from_rs(rs_file)
    if cid:
        return name, _normalize_xpath(f"//*[@id='{cid}']")
    if not CHKBX_SUFFIX.search(name):
        return name, None
    key = CHKBX_SUFFIX.sub("", name)
    fixed = _apply_checkbox_fixup(folder_name, ui_label, key, name, "")
    if fixed:
        return name, fixed
    return name, None


def _ui_dropdown(label: str) -> str:
    return f"//*[@id='{label}' and @role='button']"


def _load_katalon_folder(katalon_filter: Path, folder_name: str, ui_label: str) -> dict[str, str]:
    folder = katalon_filter / folder_name
    out = {}
    if not folder.is_dir():
        return out
    for rs in sorted(folder.glob("*.rs")):
        name, xp = read_checkbox_locator(rs, folder_name=folder_name, ui_label=ui_label)
        if xp:
            out[name] = xp
    return out


def _checkboxes_from_folder(katalon_filter: Path, folder_name: str, ui_label: str) -> OrderedDict[str, str]:
    elems = _load_katalon_folder(katalon_filter, folder_name, ui_label)
    chk = OrderedDict()
    for name, xp in sorted(elems.items()):
        if not CHKBX_SUFFIX.search(name):
            continue
        key = CHKBX_SUFFIX.sub("", name)
        chk[key] = _apply_checkbox_fixup(folder_name, ui_label, key, name, xp)
    return chk


def _apply_checkbox_fixup(
    folder_name: str, ui_label: str, key: str, obj_name: str, xp: str
) -> str:
    if "checkbox_" in xp:
        return xp
    if folder_name == "StageOfDisease" and key in STAGE_VALUE_BY_KEY:
        val = STAGE_VALUE_BY_KEY[key]
        return f"//*[@id='checkbox_{ui_label}_{val}']"
    if folder_name == "StudyType":
        if key in STUDY_TYPE_VALUE_BY_KEY:
            val = STUDY_TYPE_VALUE_BY_KEY[key]
            return f"//*[@id='checkbox_{ui_label}_{val}']"
        if key.endswith("Transcrip"):
            return f"//*[@id='checkbox_{ui_label}_Transcriptomics']"
    return xp


def _plain(obj):
    if isinstance(obj, OrderedDict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def _write_yaml(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        fh.write(f"# ICDC object repository ({path.name})\n")
        yaml.safe_dump(_plain(doc), fh, sort_keys=False, allow_unicode=True, width=4096)


def build_filter_yamls(katalon_canine: Path) -> None:
    filter_root = katalon_canine / "Object Repository" / "Canine" / "Filter"
    pages: dict[str, OrderedDict] = {
        "cases": OrderedDict(),
        "samples": OrderedDict(),
        "files": OrderedDict(),
    }
    for section, folder_name, group_key, ui_label in FILTER_ORDER:
        if folder_name is None:
            checkboxes = PROGRAM_CHECKBOXES
        else:
            checkboxes = _checkboxes_from_folder(filter_root, folder_name, ui_label)
            if not checkboxes:
                raise SystemExit(f"No checkboxes in Filter/{folder_name}")
        pages[section][group_key] = {
            "facet": FACET_SECTION[section],
            "dropdown": _ui_dropdown(ui_label),
            "checkboxes": dict(checkboxes),
        }
    _write_yaml(OUT / "filters" / "cases.yaml", {"page": "Filters/Cases", "groups": pages["cases"]})
    _write_yaml(OUT / "filters" / "samples.yaml", {"page": "Filters/Samples", "groups": pages["samples"]})
    _write_yaml(OUT / "filters" / "files.yaml", {"page": "Filters/Files", "groups": pages["files"]})


def remove_legacy_filter_yamls() -> None:
    for legacy in (OUT / "filters.yaml", OUT / "filter.yaml"):
        if legacy.is_file():
            legacy.unlink()
    filt = OUT / "filters"
    if not filt.is_dir():
        return
    keep = {"cases.yaml", "samples.yaml", "files.yaml"}
    for f in filt.glob("*.yaml"):
        if f.name not in keep:
            f.unlink()


def patch_statbar() -> None:
    path = OUT / "statbar.yaml"
    if not path.is_file():
        path = OUT / "stat_bar.yaml"
    if not path.is_file():
        return
    doc = yaml.safe_load(path.read_text()) or {}
    elements = doc.get("elements") or {}
    ordered = OrderedDict()
    for i, key in enumerate(STATBAR_ORDER, start=1):
        if key in elements:
            ordered[key] = f'//*[@id="statsbar_count_{i}"]'
    if ordered:
        doc["elements"] = dict(ordered)
        _write_yaml(path, doc)


def patch_result_tabs() -> None:
    for candidate in (OUT / "result_tabs.yaml", OUT / "canine_results.yaml", OUT / "root.yaml"):
        if not candidate.is_file():
            continue
        doc = yaml.safe_load(candidate.read_text()) or {}
        elements = doc.get("elements") or {}
        changed = False
        for key, xp in RESULT_TAB_OVERRIDES.items():
            if key in elements:
                elements[key] = xp
                changed = True
        if changed:
            doc["elements"] = dict(sorted(elements.items()))
            _write_yaml(candidate, doc)


def _validate_filter_yamls() -> None:
    bad = []
    for yf in (OUT / "filters").glob("*.yaml"):
        text = yf.read_text()
        if "contains(text()" in text or "contains(text()," in text:
            bad.append(yf.name)
    if bad:
        raise SystemExit(f"Legacy text-based checkbox xpaths remain in: {', '.join(bad)}")


def main() -> int:
    if not KATALON.is_dir():
        raise SystemExit(f"Katalon project not found: {KATALON}")
    if not ICDC_FE.is_dir():
        raise SystemExit(f"ICDC frontend not found: {ICDC_FE}")
    if OUT.exists():
        shutil.rmtree(OUT)
    convert_app(KATALON, "ICDC", OUT.parent)
    remove_legacy_filter_yamls()
    build_filter_yamls(KATALON)
    patch_statbar()
    patch_result_tabs()
    _validate_filter_yamls()
    from Commons.object_repository import ObjectRepository

    repo = ObjectRepository("ICDC")
    print(f"ICDC: {len(repo._elements)} elements, {len(repo._groups)} filter groups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
