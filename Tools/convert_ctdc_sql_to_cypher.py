#!/usr/bin/env python3
"""
Replace SQL in InputFiles/CTDC/TC*.xlsx with Memgraph Cypher (StatQuery + 4 tab rows).

    python Tools/convert_ctdc_sql_to_cypher.py
    python Tools/convert_ctdc_sql_to_cypher.py --dry-run

Skips CTDC_StaticData.xlsx and TC01_CTDC_LocalSearch*.xlsx (legacy non-CTDC graph).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Tools" / "cypher"))

import ctdc_cypher as cc  # noqa: E402
from ctdc_cypher import parse_sql_filters  # noqa: E402

INPUT = ROOT / "InputFiles" / "CTDC"
SKIP = {"CTDC_StaticData.xlsx"}


def _cell_map(ws) -> dict:
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=False):
        key = row[0].value
        if not key:
            continue
        out[str(key).strip()] = row
    return out


def convert_workbook(path: Path, dry_run: bool) -> bool:
    wb = openpyxl.load_workbook(path)
    ws = wb.worksheets[0]
    rows = _cell_map(ws)
    part_row = rows.get("ParticipantsTab")
    if not part_row:
        return False
    part_sql = str(part_row[1].value or "")
    if part_sql.lstrip().upper().startswith("MATCH"):
        wb.close()
        return False
    pf = parse_sql_filters(part_sql)
    pf_stat = type(pf)(
        study_id=pf.study_id,
        predicates=pf.predicates,
        require_file_name=False,
    )
    pf_files = pf
    files_row = rows.get("FilesTab")
    if files_row and files_row[1].value:
        ff = parse_sql_filters(str(files_row[1].value))
        extra = tuple(p for p in ff.predicates if p not in pf.predicates)
        pf_files = type(pf)(
            study_id=pf.study_id,
            predicates=pf.predicates + extra,
            require_file_name=ff.require_file_name,
        )
    cy = {
        "StatQuery": cc.stat_query(pf_stat),
        "ParticipantsTab": cc.participants_tab_query(pf),
        "BiospecimensTab": cc.biospecimens_tab_query(pf),
        "FilesTab": cc.files_tab_query(pf_files),
        "StudyFilesTab": cc.study_files_tab_query(pf),
    }
    if dry_run:
        print(f"{path.name}: would write Cypher ({len(cy)} queries)")
        return True
    col_query = 1  # TabQuery column B
    for tab_name, cypher in cy.items():
        if tab_name == "StatQuery":
            part_row[2].value = cypher
            continue
        if tab_name in rows:
            rows[tab_name][col_query].value = cypher
        else:
            ws.append([tab_name, cypher, None, None, None])
    wb.save(path)
    wb.close()
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--input", type=Path, default=INPUT)
    args = ap.parse_args()
    n = 0
    for path in sorted(args.input.glob("TC*.xlsx")):
        if path.name in SKIP or "LocalSearch" in path.name:
            print(f"skip {path.name}")
            continue
        if convert_workbook(path, args.dry_run):
            n += 1
            if not args.dry_run:
                print(f"updated {path.name}")
    print(f"done: {n} workbook(s)")


if __name__ == "__main__":
    main()
