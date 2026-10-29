#!/usr/bin/env python3
"""Build ObjectRepository/INS/Programs/*.yaml and DataSets/repository.yaml from Katalon INS."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Tools.convert_object_repository import read_locator  # noqa: E402

KATALON = ROOT.parent / "Commons_Automation" / "Object Repository" / "INS"
PROGRAMS_OUT = ROOT / "ObjectRepository" / "INS" / "Programs"
DATASETS_OUT = ROOT / "ObjectRepository" / "INS" / "DataSets"

CHKBX = re.compile(r"[-_]Chkbx$")
DDN = re.compile(r"[-_]Ddn$")


def _token(name: str) -> str:
    return CHKBX.sub("", name)


def _load_folder(folder: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for rs in sorted(folder.glob("*.rs")):
        name, xp = read_locator(rs)
        if xp:
            out[name] = xp
    return out


def _write(page: str, groups: dict) -> None:
    PROGRAMS_OUT.mkdir(parents=True, exist_ok=True)
    path = PROGRAMS_OUT / f"{page.lower()}.yaml"
    doc = {"page": f"Filters/{page}", "groups": groups}
    with open(path, "w") as fh:
        fh.write(f"# INS Explore filters ({page})\n")
        yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True, width=10_000)


def build_cancer_type() -> None:
    folder = KATALON / "Filters" / "CancerType"
    elems = _load_folder(folder)
    ddn = next((xp for n, xp in elems.items() if DDN.search(n)), '//*[@id="Cancer Type"]')
    checkboxes = {_token(n): xp for n, xp in elems.items() if CHKBX.search(n)}
    _write(
        "CancerType",
        {
            "CancerType/CancerType": {
                "dropdown": ddn,
                "checkboxes": dict(sorted(checkboxes.items())),
            }
        },
    )


def build_special_topic() -> None:
    folder = KATALON / "Filters" / "SpecialTopic"
    elems = _load_folder(folder)
    ddn = next((xp for n, xp in elems.items() if DDN.search(n)), '//*[@id="Special Topic"]')
    checkboxes = {_token(n): xp for n, xp in elems.items() if CHKBX.search(n)}
    _write(
        "SpecialTopic",
        {
            "SpecialTopic/SpecialTopic": {
                "dropdown": ddn,
                "checkboxes": dict(sorted(checkboxes.items())),
            }
        },
    )


def build_datasets_repository() -> None:
    folder = KATALON / "DataSets" / "Repository"
    elems = _load_folder(folder)
    checkboxes = {_token(n): xp for n, xp in elems.items() if CHKBX.search(n)}
    DATASETS_OUT.mkdir(parents=True, exist_ok=True)
    path = DATASETS_OUT / "repository.yaml"
    doc = {
        "page": "DataSets/Repository",
        "groups": {
            "DataSets/Repository": {
                "checkboxes": dict(sorted(checkboxes.items())),
            }
        },
    }
    with open(path, "w") as fh:
        fh.write("# INS Explore Datasets — repository filter checkboxes\n")
        yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True, width=10_000)


def main() -> None:
    build_cancer_type()
    build_special_topic()
    build_datasets_repository()
    print(f"Wrote INS Programs filter YAML under {PROGRAMS_OUT}")
    print(f"Wrote INS DataSets repository YAML under {DATASETS_OUT}")


if __name__ == "__main__":
    main()
