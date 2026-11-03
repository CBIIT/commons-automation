"""Replace phs003162 stat bar `0 AS files` with cohort sample CALL + dcf_indexd_guid rollup."""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl

from Commons.query_reader import read_query_file

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "InputFiles" / "C3DC"
PHS = "phs003162"
SKIP = {"TC01_C3DC_phs003162_StudyPhase-Completed.xlsx"}  # study-scoped fast stat

FILE_EDGE = (
    "-[:of_sequencing_file|of_clinical_measure_file|of_cytogenomic_file|of_generic_file|"
    "of_methylation_array_file|of_pathology_file|of_radiology_file]->"
)

# Per-participant derived-sample branch (count pass only).
SAMPLE_CALL_BODY = """
  WITH p
  MATCH (sm:sample)-[:of_sample]->(p)
  RETURN sm
  UNION
  WITH p
  MATCH (parent:sample)-[:of_sample]->(p)
  MATCH (sm:sample)-[:of_sample]->(:cell_line)-[:of_cell_line]->(parent)
  RETURN sm
  UNION
  WITH p
  MATCH (parent:sample)-[:of_sample]->(p)
  MATCH (sm:sample)-[:of_sample]->(:pdx)-[:of_pdx]->(parent)
  RETURN sm"""

# Sample counts: CALL per cohort row. Files: four small CALLs (direct / CL / PDX / participant)
# — avoids UNWIND sample_nodes (532× OPTIONAL MATCH, ~3 min on QA) while keeping 4982 GUIDs.
FILE_GUID_CALLS = f"""
CALL {{
  WITH cohort_participants
  UNWIND cohort_participants AS p
  MATCH (sm:sample)-[:of_sample]->(p)
  MATCH (f){FILE_EDGE}(sm)
  RETURN collect(DISTINCT f.dcf_indexd_guid) AS g1
}}
CALL {{
  WITH cohort_participants
  UNWIND cohort_participants AS p
  MATCH (parent:sample)-[:of_sample]->(p)
  MATCH (sm:sample)-[:of_sample]->(:cell_line)-[:of_cell_line]->(parent)
  MATCH (f){FILE_EDGE}(sm)
  RETURN collect(DISTINCT f.dcf_indexd_guid) AS g2
}}
CALL {{
  WITH cohort_participants
  UNWIND cohort_participants AS p
  MATCH (parent:sample)-[:of_sample]->(p)
  MATCH (sm:sample)-[:of_sample]->(:pdx)-[:of_pdx]->(parent)
  MATCH (f){FILE_EDGE}(sm)
  RETURN collect(DISTINCT f.dcf_indexd_guid) AS g3
}}
CALL {{
  WITH cohort_participants
  UNWIND cohort_participants AS p
  OPTIONAL MATCH (fp)-[:of_clinical_measure_file|of_generic_file|of_radiology_file]->(p)
  RETURN collect(DISTINCT fp.dcf_indexd_guid) AS g4
}}
WITH studies, participants, samples, g1, g2, g3, g4, g1 + g2 + g3 + g4 AS guids
UNWIND guids AS guid
RETURN studies, participants, samples, count(DISTINCT guid) AS files"""

STAT_TAIL = f"""
WITH DISTINCT p, s
CALL {{
{SAMPLE_CALL_BODY}
}}
WITH count(DISTINCT s) AS studies,
     count(DISTINCT p) AS participants,
     count(DISTINCT sm) AS samples,
     collect(DISTINCT p) AS cohort_participants
{FILE_GUID_CALLS}"""

def _sample_facet_file_guid_calls(samples_tab: str) -> str:
    """One file CALL per SamplesTab UNION branch (no UNWIND cohort_samples)."""
    body = _samples_tab_call_body(samples_tab)
    branches = re.split(r"\n\s*UNION\s*\n", body)
    calls: list[str] = []
    g_names: list[str] = []
    for i, branch in enumerate(branches, 1):
        branch = re.sub(r"RETURN\s+sm,\s+p,\s+s\s*$", "", branch.strip(), flags=re.MULTILINE).strip()
        g = f"g{i}"
        g_names.append(g)
        calls.append(
            f"""CALL {{
{branch}
  MATCH (f){FILE_EDGE}(sm)
  RETURN collect(DISTINCT f.dcf_indexd_guid) AS {g}
}}"""
        )
    g_part = "g_part"
    g_names.append(g_part)
    calls.append(
        f"""CALL {{
  WITH cohort_participants
  UNWIND cohort_participants AS p
  OPTIONAL MATCH (fp)-[:of_clinical_measure_file|of_generic_file|of_radiology_file]->(p)
  RETURN collect(DISTINCT fp.dcf_indexd_guid) AS {g_part}
}}"""
    )
    g_sum = " + ".join(g_names)
    tail = f"""
WITH studies, participants, samples, {", ".join(g_names)}, {g_sum} AS guids
UNWIND guids AS guid
RETURN studies, participants, samples, count(DISTINCT guid) AS files"""
    return "\n".join(calls) + tail


def _cohort_anchor_stat(participants_tab: str) -> str:
    """First MATCH..WITH DISTINCT p,s from ParticipantsTab (StatQuery uses same cohort)."""
    for pattern in (
        r"(MATCH \(d:diagnosis\).*?WITH DISTINCT p, s)",
        r"(MATCH \(sm:sample\).*?WITH DISTINCT p, s)",
        r"(MATCH \(p:participant\).*?WITH DISTINCT p, s)",
    ):
        m = re.search(pattern, participants_tab, re.DOTALL)
        if m:
            return m.group(1)
    m = re.search(
        r"(MATCH \(p:participant\).*?WITH DISTINCT p, s)",
        participants_tab,
        re.DOTALL,
    )
    if m:
        return m.group(1)
    m = re.search(
        r"(MATCH \(p:participant\).*?WHERE s\.dbgap_accession = 'phs003162'[^\n]*\n(?:  AND[^\n]+\n)*)",
        participants_tab,
        re.DOTALL,
    )
    if m:
        head = m.group(1).rstrip()
        if "WITH DISTINCT" not in head:
            return head + "WITH DISTINCT p, s"
        return head
    raise ValueError("Could not build stat cohort anchor from ParticipantsTab")


def _samples_tab_call_body(samples_tab: str) -> str:
    m = re.search(r"CALL\s*\{(.*)\}\s*WITH DISTINCT sm", samples_tab, re.DOTALL)
    if not m:
        raise ValueError("Could not parse SamplesTab CALL { … } body")
    return m.group(1).strip()


def _is_sample_facet_cohort(participants_tab: str) -> bool:
    head = participants_tab.split("WITH DISTINCT")[0]
    return "MATCH (sm:sample)" in head


def _sample_facet_participant_head(participants_tab: str) -> str:
    """Studies/participants from ParticipantsTab anchor (direct sample filter); avoids UNION for counts."""
    anchor = _cohort_anchor_stat(participants_tab)
    head = anchor.split("WITH DISTINCT p, s")[0].rstrip()
    return f"""{head}
WITH count(DISTINCT s) AS studies,
     count(DISTINCT p) AS participants,
     collect(DISTINCT p) AS cohort_participants"""


def make_stat(participants_tab: str, samples_tab: str = "") -> str:
    if _is_sample_facet_cohort(participants_tab):
        if not samples_tab:
            raise ValueError("Sample-facet cohort requires SamplesTab")
        body = _samples_tab_call_body(samples_tab)
        file_calls = _sample_facet_file_guid_calls(samples_tab)
        head = _sample_facet_participant_head(participants_tab)
        return f"""{head}
CALL {{
{body}
}}
WITH studies, participants, cohort_participants, count(DISTINCT sm) AS samples
{file_calls}"""
    anchor = _cohort_anchor_stat(participants_tab)
    if "WITH DISTINCT p, s" in anchor:
        head = anchor.split("WITH DISTINCT p, s")[0].rstrip()
        return head + STAT_TAIL
    return anchor.rstrip() + STAT_TAIL


def patch_workbook(path: Path) -> None:
    qf = read_query_file("C3DC", path.name)
    participants = qf.query_for_tab("ParticipantsTab")
    samples = qf.query_for_tab("SamplesTab") if "SamplesTab" in qf.queries_by_tab else ""
    stat = make_stat(participants, samples)
    wb = openpyxl.load_workbook(path)
    for row in wb.active.iter_rows(min_row=2):
        if row[0].value == "ParticipantsTab":
            row[2].value = stat  # StatQuery column
            break
    wb.save(path)
    wb.close()


def main() -> None:
    for path in sorted(IN.glob(f"*_{PHS}_*.xlsx")):
        if path.name in SKIP:
            print("skip", path.name)
            continue
        patch_workbook(path)
        print("patched", path.name)


if __name__ == "__main__":
    main()
