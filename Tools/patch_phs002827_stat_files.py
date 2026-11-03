"""Replace phs002827 stat `0 AS files` with cohort dcf_indexd_guid rollup (Explore data-release stat bar)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import openpyxl

from Commons.query_reader import read_query_file

# Reuse sample-facet stat builder from phs003162 patcher.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_phs003162_stat_files import (  # noqa: E402
    _is_sample_facet_cohort,
    make_stat as make_sample_facet_stat,
)

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "InputFiles" / "C3DC"
PHS = "phs002827"

FILE_EDGE = (
    "-[:of_sequencing_file|of_clinical_measure_file|of_cytogenomic_file|of_generic_file|"
    "of_methylation_array_file|of_pathology_file|of_radiology_file]->"
)

def _sample_sm_where(participants_tab: str) -> str:
    m = re.search(r"AND (sm2?\.\w+[^\n]+)", participants_tab.split("WITH DISTINCT")[0])
    return f"\n  WHERE {m.group(1).strip()}" if m else ""


def _participant_file_tail(sample_sm_where: str = "") -> str:
    return f"""
CALL {{
  WITH cohort_participants
  UNWIND cohort_participants AS p
  MATCH (sm:sample)-[:of_sample]->(p){sample_sm_where}
  MATCH (f){FILE_EDGE}(sm)
  RETURN collect(DISTINCT f.dcf_indexd_guid) AS g1
}}
CALL {{
  WITH cohort_participants
  UNWIND cohort_participants AS p
  OPTIONAL MATCH (fp)-[:of_clinical_measure_file|of_generic_file|of_radiology_file]->(p)
  RETURN collect(DISTINCT fp.dcf_indexd_guid) AS g2
}}
WITH studies, participants, samples, g1, g2, g1 + g2 AS guids
UNWIND guids AS guid
RETURN studies, participants, samples, count(DISTINCT guid) AS files"""


PARTICIPANT_FILE_TAIL = _participant_file_tail()


def _strip_old_stat_tail(stat: str) -> str:
    stat = re.sub(r"//[^\n]*\n", "", stat)
    head = re.split(r"\nOPTIONAL MATCH", stat, maxsplit=1)[0].strip()
    if "WITH DISTINCT p, s" not in head:
        head = head + "\nWITH DISTINCT p, s"
    return head


def make_participant_cohort_stat(stat: str, sample_match: str) -> str:
    head = _strip_old_stat_tail(stat)
    return f"""{head}
{sample_match}
WITH count(DISTINCT s) AS studies,
     count(DISTINCT p) AS participants,
     count(DISTINCT sm) AS samples,
     collect(DISTINCT p) AS cohort_participants
{PARTICIPANT_FILE_TAIL}"""


def make_stat_from_workbook(path: Path) -> str:
    qf = read_query_file("C3DC", path.name)
    old = qf.stat_bar_query
    participants = qf.query_for_tab("ParticipantsTab")
    samples_tab = qf.query_for_tab("SamplesTab") if "SamplesTab" in qf.queries_by_tab else ""
    if _is_sample_facet_cohort(participants) and "CALL {" in samples_tab:
        return make_sample_facet_stat(participants, samples_tab)
    if _is_sample_facet_cohort(participants):
        sm_where = _sample_sm_where(participants)
        sample_match = f"OPTIONAL MATCH (sm:sample)-[:of_sample]->(p){sm_where}"
        head = _strip_old_stat_tail(old)
        tail = _participant_file_tail(sm_where)
        return f"""{head}
{sample_match}
WITH count(DISTINCT s) AS studies,
     count(DISTINCT p) AS participants,
     count(DISTINCT sm) AS samples,
     collect(DISTINCT p) AS cohort_participants
{tail}"""
    # TC06-style: optional sample alias / extra WHERE on sample count.
    m = re.search(
        r"(OPTIONAL MATCH \(sm2?:sample\)[^\n]+\n(?:WHERE[^\n]+\n)?)",
        old,
        re.IGNORECASE,
    )
    sample_match = m.group(1).strip() if m else "OPTIONAL MATCH (sm:sample)-[:of_sample]->(p)"
    return make_participant_cohort_stat(old, sample_match)


def patch_workbook(path: Path) -> None:
    stat = make_stat_from_workbook(path)
    wb = openpyxl.load_workbook(path)
    for row in wb.active.iter_rows(min_row=2):
        if row[0].value == "ParticipantsTab":
            row[2].value = stat
            break
    wb.save(path)
    wb.close()


def main() -> None:
    for path in sorted(IN.glob(f"*_{PHS}_*.xlsx")):
        patch_workbook(path)
        print("patched", path.name)


if __name__ == "__main__":
    main()
