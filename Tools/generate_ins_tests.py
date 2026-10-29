#!/usr/bin/env python3
"""Generate pytest INS tests from Katalon Scripts/INS_TestCases/*.groovy."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KATALON_SCRIPTS = ROOT.parent / "Commons_Automation" / "Scripts" / "INS_TestCases"
OUT = ROOT / "Testcases" / "INS"
# Katalon INS_TestCases/CancerType|SpecialTopic → Testcases/INS/Programs/…
PROGRAMS_KATALON_DIRS = frozenset({"CancerType", "SpecialTopic"})

TAB_FROM_TSV = {
    "TsvDataPrograms": "Programs",
    "TsvDataProjects": "Projects",
    "TsvDataGrants": "Grants",
    "TsvDataPublications": "Publications",
}

RE_XLSX = re.compile(r"RunKatalon'\('([^']+\.xlsx)'\)")
RE_FILTER = re.compile(
    r"INS/Filters/(CancerType|SpecialTopic)/([A-Za-z0-9]+)-Chkbx"
)
RE_DATASETS_REPO = re.compile(r"INS/DataSets/Repository/([A-Za-z0-9]+)-Chkbx")
RE_ACTIVE_TSV = re.compile(r"multiFunction\([^)]*'(TsvData\w+)'")


def _active_lines(text: str) -> str:
    out = []
    for line in text.splitlines():
        if line.strip().startswith("//"):
            continue
        out.append(line)
    return "\n".join(out)


RE_STATIC = re.compile(r"verifyStaticData\([\"']([^\"']+)[\"']\)")


def _parse_groovy(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "verifyStaticData" in text:
        return {"kind": "static", "stem": path.parent.name, "sheets": RE_STATIC.findall(text)}
    m = RE_XLSX.search(text)
    if not m:
        return None
    xlsx = m.group(1)
    active = _active_lines(text)
    nav = "programs"
    if "INS/Navbar/Datasets-Btn" in active:
        nav = "datasets"
    fm = RE_FILTER.search(active)
    if fm:
        facet, token = fm.group(1), fm.group(2)
        group = f"{facet}/{facet}"
        filter_call = f'ins.select_filter("{group}", "{token}")'
    else:
        dm = RE_DATASETS_REPO.search(active)
        if dm:
            filter_call = f'ins.select_filter("DataSets/Repository", "{dm.group(1)}")'
        else:
            filter_call = None
    tabs = []
    for tsv in RE_ACTIVE_TSV.findall(active):
        tab = TAB_FROM_TSV.get(tsv)
        if tab and tab not in tabs:
            tabs.append(tab)
    if not tabs and nav == "programs":
        tabs = ["Programs", "Projects"]
    return {
        "kind": "explore",
        "xlsx": xlsx,
        "nav": nav,
        "filter_call": filter_call,
        "tabs": tabs,
        "stem": path.parent.name,
    }


def _test_body(info: dict) -> str:
    if info.get("kind") == "static":
        lines = []
        sheets = info.get("sheets") or []
        if sheets:
            lines.append(f'    ins.verify_static_data("{sheets[0]}")')
        if len(sheets) > 1:
            lines.append('    ins.click("Navbar/About-Btn")')
            lines.append('    ins.click("Navbar/About-INS-Btn")')
            lines.append(f'    ins.verify_static_data("{sheets[1]}")')
        lines.append("    ins.assert_no_failures()")
        return "\n".join(lines)
    if info.get("stem", "").startswith("TC00_INS_QuickRun"):
        return "    pytest.skip('INS QuickRun is a Katalon batch harness')"
    lines = [
        f'    ins.load_query_file("{info["xlsx"]}")',
    ]
    if info["nav"] == "datasets":
        lines.append("    ins.open_datasets()")
    else:
        lines.append("    ins.open_programs()")
    if info["filter_call"]:
        lines.append(f"    {info['filter_call']}")
    if info["nav"] == "datasets":
        return "    pytest.skip('INS Datasets TSV compare not migrated yet')"
    lines.append("    ins.read_statbar()")
    for tab in info["tabs"]:
        lines.append(f'    ins.verify_tab("{tab}")')
    lines.append("    ins.assert_no_failures()")
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for script in sorted(KATALON_SCRIPTS.rglob("Script*.groovy")):
        info = _parse_groovy(script)
        if not info:
            continue
        if info.get("kind") == "static":
            continue
        if info.get("stem", "").startswith("TC00_INS_QuickRun"):
            continue
        func = info["stem"].replace("-", "_")
        if not func.startswith("test_"):
            func = f"test_{func}"
        rel_dir = script.parent.relative_to(KATALON_SCRIPTS)
        if rel_dir.parts and rel_dir.parts[0] in PROGRAMS_KATALON_DIRS:
            rel_dir = Path("Programs") / rel_dir
        out_dir = OUT / rel_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{func}.py"
        body = _test_body(info)
        skip_datasets = info.get("nav") == "datasets"
        skip_deco = "\n@pytest.mark.skip(reason='INS Datasets TSV compare not migrated yet')" if skip_datasets else ""
        content = f'''"""Migrated from Katalon {script.relative_to(KATALON_SCRIPTS.parent)}."""

import pytest


@pytest.mark.ins
@pytest.mark.regression{skip_deco}
def {func}(ins):
{body}
'''
        out_file.write_text(content, encoding="utf-8")
        count += 1
    init_dirs = {p.parent for p in OUT.rglob("test_*.py")}
    for d in sorted(init_dirs):
        init = d / "__init__.py"
        if not init.exists():
            init.touch()
    if not (OUT / "__init__.py").exists():
        (OUT / "__init__.py").touch()
    print(f"Generated {count} INS tests under {OUT}")


if __name__ == "__main__":
    main()
