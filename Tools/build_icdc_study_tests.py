#!/usr/bin/env python3
"""Sync ICDC input workbooks (flat InputFiles/ICDC/) and generate pytest cases (TC01–TC07)."""
from __future__ import annotations

import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KATALON_IN = ROOT.parent / "Commons_Automation" / "InputFiles" / "ICDC"
SCRIPTS = ROOT.parent / "Commons_Automation" / "Scripts" / "Canine_TestCases" / "Studies"
INPUT_OUT = ROOT / "InputFiles" / "ICDC"
TESTS_OUT = ROOT / "Testcases" / "ICDC" / "studies"

FOLDER_TO_GROUP = {
    "StudyType": "Cases/StudyType",
    "Biobank": "Cases/Biobank",
    "Breed": "Cases/Breed",
    "Diagnosis": "Cases/Diagnosis",
    "PrimDiseaseSite": "Cases/PrimaryDiseaseSite",
    "StageOfDisease": "Cases/StageOfDisease",
    "ResponseToTreatment": "Cases/ResponseToTreatment",
    "Sex": "Cases/Sex",
    "NeuteredStatus": "Cases/NeuteredStatus",
    "SampleSite": "Samples/SampleSite",
    "SampleType": "Samples/SampleType",
    "SamplePathology": "Samples/SamplePathology",
    "FileAssociation": "Files/FileAssociation",
    "FileType": "Files/FileType",
    "FileFormat": "Files/FileFormat",
}

CHKBX_RE = re.compile(r"Filter/([^/]+)/([^'\"()]+)_Chkbx")
RUN_KATALON_RE = re.compile(r"RunKatalon'\('([^']+\.xlsx)'\)")
XLSX_RE = re.compile(r"^(TC\d+)_ICDC_([A-Za-z0-9-]+)_(.+)\.xlsx$", re.I)


def _py_name(stem: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_")


def _find_script_dir(tc_stem: str) -> Path | None:
    """Locate Katalon Script folder for a test case name (TC01_ICDC_...)."""
    name = tc_stem.split(".")[0]
    hits = [p for p in SCRIPTS.rglob(name) if p.is_dir()]
    if not hits:
        m = re.match(r"(TC\d+)_ICDC_([^_]+)_", name)
        if m:
            tc, study = m.group(1), m.group(2)
            prefix = f"{tc}_ICDC_{study}_"
            hits = [
                p
                for p in SCRIPTS.rglob(f"{tc}_ICDC_{study}_*")
                if p.is_dir() and p.name.startswith(prefix)
            ]
    if not hits:
        return None
    hits.sort(key=lambda p: (0 if "Studies" in p.parts else 1, len(p.parts)))
    return hits[0]


def _parse_groovy(script_dir: Path) -> tuple[str | None, str | None, str | None, str | None]:
    for g in script_dir.glob("Script*.groovy"):
        text = g.read_text(encoding="utf-8", errors="replace")
        xlsx_m = RUN_KATALON_RE.search(text)
        xlsx = xlsx_m.group(1) if xlsx_m else None
        matches = CHKBX_RE.findall(text)
        study_key = None
        facet_folder, facet_chk = None, None
        for folder, chk in matches:
            if folder == "Study":
                if chk.startswith("Canine_Filter_Study-"):
                    study_key = chk
                continue
            facet_folder, facet_chk = folder, chk
        if facet_folder and facet_chk:
            return xlsx, study_key, facet_folder, facet_chk
        return xlsx, study_key, None, None
    return None, None, None, None


def _collect_xlsx_by_study() -> dict[str, dict[str, Path]]:
    by_study: dict[str, dict[str, Path]] = defaultdict(dict)
    sources = [INPUT_OUT, KATALON_IN]
    seen_names: set[str] = set()
    for base in sources:
        if not base.is_dir():
            continue
        for f in base.rglob("*.xlsx"):
            if "Copy" in f.name or f.name in seen_names:
                continue
            m = XLSX_RE.match(f.name)
            if not m:
                continue
            tc, study, _ = m.group(1), m.group(2), m.group(3)
            if int(tc[2:]) > 7:
                continue
            if tc not in by_study[study]:
                by_study[study][tc] = f
                seen_names.add(f.name)
    return by_study


def _write_init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    init = path / "__init__.py"
    if not init.exists():
        init.write_text("")


def _render_test(
    tc_stem: str,
    study: str,
    input_rel: str,
    study_key: str,
    group: str,
    checkbox: str,
    description: str,
) -> str:
    fn = "test_" + _py_name(tc_stem)
    return f'''"""{description}"""

import pytest

_INPUT = "{input_rel}"


@pytest.mark.icdc
@pytest.mark.regression
def {fn}(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study({study_key!r})
    icdc.select_filter("{group}", {checkbox!r})
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
'''


def build() -> None:
    by_study = _collect_xlsx_by_study()
    _write_init(TESTS_OUT)
    _write_init(TESTS_OUT)  # studies parent already Testcases/ICDC

    summary = []
    for study in sorted(by_study):
        study_dir_tests = TESTS_OUT / study
        _write_init(study_dir_tests)

        tcs = sorted(by_study[study], key=lambda x: int(x[2:]))
        n_written = 0
        for tc in tcs:
            src = by_study[study][tc]
            dest = INPUT_OUT / src.name
            if src.resolve() != dest.resolve():
                shutil.copy2(src, dest)

            tc_stem = src.stem
            script_dir = _find_script_dir(tc_stem)
            xlsx, study_key, facet_folder, facet_chk = (
                _parse_groovy(script_dir) if script_dir else (None, None, None, None)
            )
            study_key = study_key or f"Canine_Filter_Study-{study}"
            if not facet_folder or not facet_chk:
                summary.append(f"SKIP test (no groovy filter): {study}/{tc_stem}")
                continue
            group = FOLDER_TO_GROUP.get(facet_folder)
            if not group:
                summary.append(f"SKIP test (unknown facet folder {facet_folder}): {study}/{tc_stem}")
                continue

            input_rel = dest.name
            suffix = tc_stem.split(f"_ICDC_{study}_", 1)[-1] if f"_ICDC_{study}_" in tc_stem else tc_stem
            desc = (
                f"Open Explore for study {study}, filter {suffix.replace('-', ' ')}, "
                f"then compare stat bar and result tabs to DB queries."
            )
            out_py = study_dir_tests / f"test_{_py_name(tc_stem)}.py"
            out_py.write_text(
                _render_test(tc_stem, study, input_rel, study_key, group, facet_chk, desc)
            )
            n_written += 1
        summary.append(f"{study}: {len(tcs)} input(s), {n_written} test(s)")

    for line in summary:
        print(line)


def _ensure_cypher_workbook(path: Path) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "convert_icdc_sql_to_cypher",
        ROOT / "Tools" / "convert_icdc_sql_to_cypher.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    mod.convert_workbook(path, dry_run=False)


if __name__ == "__main__":
    build()
    for path in sorted(INPUT_OUT.glob("TC*.xlsx")):
        _ensure_cypher_workbook(path)
