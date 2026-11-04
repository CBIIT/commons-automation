"""One-off: optimize phs002430 InputFiles Cypher (stat + tabs). Safe cohort prefilter patterns."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "InputFiles" / "C3DC"

STUDY_FIRST = (
    "MATCH (s:study)\n"
    "WHERE s.dbgap_accession = 'phs002430'\n"
)

STAT_TAIL = """
WITH DISTINCT p, s
OPTIONAL MATCH (sm0:sample)-[:of_sample]->(p)
OPTIONAL MATCH (parent:sample)-[:of_sample]->(p)
OPTIONAL MATCH (sm1:sample)-[:of_sample]->(:cell_line)-[:of_cell_line]->(parent)
OPTIONAL MATCH (sm2:sample)-[:of_sample]->(:pdx)-[:of_pdx]->(parent)
WITH collect(DISTINCT s) AS study_nodes,
     collect(DISTINCT p) AS cohort_p,
     collect(DISTINCT sm0) AS direct_sms,
     collect(DISTINCT sm1) AS cl_sms,
     collect(DISTINCT sm2) AS pdx_sms
WITH size(study_nodes) AS studies,
     size(cohort_p) AS participants,
     size([sm IN direct_sms + cl_sms + pdx_sms WHERE sm IS NOT NULL]) AS samples,
     cohort_p,
     [sm IN direct_sms + cl_sms + pdx_sms WHERE sm IS NOT NULL] AS sms
CALL {
  WITH cohort_p, sms
  UNWIND sms AS sm
  OPTIONAL MATCH (f)-[:of_sequencing_file|of_clinical_measure_file|of_cytogenomic_file|of_generic_file|of_methylation_array_file|of_pathology_file|of_radiology_file]->(sm)
  WITH collect(DISTINCT f.dcf_indexd_guid) AS s_guids, cohort_p
  UNWIND cohort_p AS p
  OPTIONAL MATCH (fp)-[:of_clinical_measure_file|of_generic_file|of_radiology_file]->(p)
  WITH s_guids, collect(DISTINCT fp.dcf_indexd_guid) AS p_guids
  WITH [g IN s_guids + p_guids WHERE g IS NOT NULL] AS guids
  UNWIND guids AS guid
  RETURN count(DISTINCT guid) AS files
}
RETURN studies, participants, samples, files""".strip()

EXISTS_ON_P = re.compile(
    r"AND EXISTS \{\s*MATCH \(d:diagnosis\)-\[:of_diagnosis\]->\(p\)\s*WHERE\s*([^}]+?)\s*\}\s*",
    re.DOTALL,
)

COHORT_PREFIX = (
    "MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->"
    "(:consent_group)-[:of_consent_group]->(s:study)\n"
    "WHERE s.dbgap_accession = 'phs002430'\n  AND {cond}\n"
)


def _cohort_cond_from_text(text: str) -> str | None:
    m = EXISTS_ON_P.search(text)
    if m:
        return m.group(1).strip()
    return None


def _participant_cohort_prefix(cond: str) -> str:
    return COHORT_PREFIX.format(cond=cond)


def patch_stat(stat: str, diag_cond: str | None, participant_cond: str | None) -> str:
    if participant_cond and not diag_cond:
        head = (
            STUDY_FIRST
            + "MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s)\n"
            f"WHERE {participant_cond}"
        )
        return head + "\n" + STAT_TAIL
    if diag_cond:
        head = (
            STUDY_FIRST
            + "MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->"
            "(:consent_group)-[:of_consent_group]->(s)\n"
            f"WHERE {diag_cond}"
        )
        return head + "\n" + STAT_TAIL
    return stat


def patch_participants(q: str, diag_cond: str) -> str:
    if not EXISTS_ON_P.search(q):
        return q
    rest = q.split("RETURN", 1)[1]
    return _participant_cohort_prefix(diag_cond) + "WITH DISTINCT p, s\nRETURN" + rest


def patch_studies(q: str, diag_cond: str) -> str:
    if not q.strip().startswith("MATCH (s:study)"):
        return q
    rest = q.split("WITH s", 1)[1]
    return (
        "MATCH (s:study)\nWHERE s.dbgap_accession = 'phs002430'\nWITH s" + rest
    )


def patch_genetic(q: str, diag_cond: str) -> str:
    if "genetic_analysis" not in q or not EXISTS_ON_P.search(q):
        return q
    body = q.split("WITH p, g, s,", 1)[1]
    return (
        _participant_cohort_prefix(diag_cond)
        + "WITH DISTINCT p, s\n"
        + "MATCH (g:genetic_analysis)-[:of_genetic_analysis]->(:sample)-[:of_sample]->(p)\n"
        + "WITH p, g, s," + body
    )


def patch_samples(q: str, diag_cond: str) -> str:
    if not q.strip().startswith("MATCH (sm:sample)"):
        return q
    rest = q.split("RETURN", 1)[1]
    return (
        _participant_cohort_prefix(diag_cond)
        + "WITH DISTINCT p, s\n"
        + "MATCH (sm:sample)-[:of_sample]->(p)\n"
        + "RETURN" + rest
    )


def patch_files(q: str, diag_cond: str) -> str:
    if not EXISTS_ON_P.search(q) or "MATCH (f)-" not in q:
        return q
    rest = q.split("MATCH (sm:sample)-[:of_sample]->(p)", 1)[1]
    return (
        _participant_cohort_prefix(diag_cond)
        + "WITH DISTINCT p, s\n"
        + "MATCH (sm:sample)-[:of_sample]->(p)" + rest
    )


def patch_survival(q: str, diag_cond: str) -> str:
    if "survival" not in q.lower() or not EXISTS_ON_P.search(q):
        return q
    rest = q.split("RETURN", 1)[1]
    return (
        _participant_cohort_prefix(diag_cond)
        + "WITH DISTINCT p, s\n"
        + "MATCH (sv:survival)-[:of_survival]->(p)\n"
        + "RETURN" + rest
    )


def patch_treatment_resp(q: str, diag_cond: str) -> str:
    if "treatment_response" not in q and "Treatment Response" not in q:
        return q
    if not EXISTS_ON_P.search(q):
        return q
    rest = q.split("RETURN", 1)[1]
    return (
        _participant_cohort_prefix(diag_cond)
        + "WITH DISTINCT p, s\n"
        + "MATCH (tr:treatment_response)-[:of_treatment_response]->(p)\n"
        + "RETURN" + rest
    )


def extract_filters(stat: str) -> tuple[str | None, str | None]:
    diag = _cohort_cond_from_text(stat)
    if diag:
        return diag, None
    m = re.search(
        r"MATCH \(d:diagnosis\)[^\n]+\nWHERE ([^\n]+)",
        stat,
    )
    if m:
        return m.group(1).strip(), None
    m = re.search(
        r"MATCH \(p:participant\)[^\n]+\nWHERE ([^\n]+)",
        stat,
    )
    if m and "EXISTS" not in m.group(1):
        return None, m.group(1).strip()
    m = re.search(
        r"WHERE s\.dbgap_accession = 'phs002430'\s*\n\s*AND ([^\n]+)",
        stat,
    )
    if m and "EXISTS" not in m.group(1):
        return None, m.group(1).strip()
    return None, None


def patch_workbook(path: Path) -> list[str]:
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    stat = ws.cell(2, 3).value or ""
    diag_cond, part_cond = extract_filters(stat)
    changed: list[str] = []

    new_stat = patch_stat(stat, diag_cond, part_cond)
    if new_stat != stat:
        ws.cell(2, 3).value = new_stat
        changed.append("StatQuery")

    for r in range(2, ws.max_row + 1):
        tab = ws.cell(r, 1).value
        q = ws.cell(r, 2).value
        if not q or not isinstance(q, str):
            continue
        if not diag_cond:
            continue
        new_q = q
        if tab == "ParticipantsTab":
            new_q = patch_participants(q, diag_cond)
        elif tab == "StudiesTab":
            new_q = patch_studies(q, diag_cond)
        elif tab == "GeneticAnalysisTab":
            new_q = patch_genetic(q, diag_cond)
        elif tab == "SamplesTab":
            new_q = patch_samples(q, diag_cond)
        elif tab == "FilesTab":
            new_q = patch_files(q, diag_cond)
        elif tab == "SurvivalTab":
            new_q = patch_survival(q, diag_cond)
        elif tab == "TreatmentRespTab":
            new_q = patch_treatment_resp(q, diag_cond)
        if new_q != q:
            ws.cell(r, 2).value = new_q
            changed.append(str(tab))

    if changed:
        wb.save(path)
    wb.close()
    return changed


def main() -> int:
    for path in sorted(INPUT.glob("TC*_C3DC_phs002430_*.xlsx")):
        changed = patch_workbook(path)
        if changed:
            print(path.name, "->", ", ".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
