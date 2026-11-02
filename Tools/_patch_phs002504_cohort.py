#!/usr/bin/env python3
"""One-off: replace slow EXISTS cohort filters in phs002504 C3DC workbooks."""
from __future__ import annotations

import glob
import re
from pathlib import Path

import openpyxl

BASE = Path(__file__).resolve().parents[1] / "InputFiles" / "C3DC"
STUDY = "phs002504"

# Cohort-first anchors (WITH DISTINCT p, s) and Studies-tab (WITH DISTINCT s).
COHORT_BY_SUFFIX: dict[str, tuple[str, str, str]] = {
    "AnatSite-Blood": (
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'blood' IN coalesce(d.anatomic_site, [])
WITH DISTINCT p, s""",
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'blood' IN coalesce(d.anatomic_site, [])
WITH DISTINCT s""",
        "  AND EXISTS { MATCH (d:diagnosis)-[:of_diagnosis]->(p) WHERE 'blood' IN coalesce(d.anatomic_site, []) }",
    ),
    "Diag-JuvenileMyLeNOS": (
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND d.diagnosis = 'Juvenile myelomonocytic leukemia, NOS'
WITH DISTINCT p, s""",
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND d.diagnosis = 'Juvenile myelomonocytic leukemia, NOS'
WITH DISTINCT s""",
        "  AND EXISTS { MATCH (d:diagnosis)-[:of_diagnosis]->(p) WHERE d.diagnosis = 'Juvenile myelomonocytic leukemia, NOS' }",
    ),
    "DiagnClasfSystem-ICD-O-3": (
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'ICD-O-3.2' IN coalesce(d.diagnosis_classification_system, [])
WITH DISTINCT p, s""",
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'ICD-O-3.2' IN coalesce(d.diagnosis_classification_system, [])
WITH DISTINCT s""",
        "  AND EXISTS { MATCH (d:diagnosis)-[:of_diagnosis]->(p) WHERE 'ICD-O-3.2' IN coalesce(d.diagnosis_classification_system, []) }",
    ),
    "DiagnBasis-NotReported": (
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Not Reported' IN coalesce(d.diagnosis_basis, [])
WITH DISTINCT p, s""",
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Not Reported' IN coalesce(d.diagnosis_basis, [])
WITH DISTINCT s""",
        "  AND EXISTS { MATCH (d:diagnosis)-[:of_diagnosis]->(p) WHERE 'Not Reported' IN coalesce(d.diagnosis_basis, []) }",
    ),
    "DiseasePhase-InitialDiag": (
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND d.disease_phase = 'Initial Diagnosis'
WITH DISTINCT p, s""",
        """MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND d.disease_phase = 'Initial Diagnosis'
WITH DISTINCT s""",
        "  AND EXISTS { MATCH (d:diagnosis)-[:of_diagnosis]->(p) WHERE d.disease_phase = 'Initial Diagnosis' }",
    ),
    "TrtmntType-Chemotherapy": (
        """MATCH (t:treatment_chemotherapy)-[:of_treatment_chemotherapy]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Chemotherapy' IN coalesce(t.chemotherapy_type, [])
WITH DISTINCT p, s""",
        """MATCH (t:treatment_chemotherapy)-[:of_treatment_chemotherapy]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Chemotherapy' IN coalesce(t.chemotherapy_type, [])
WITH DISTINCT s""",
        None,  # multi-line OR EXISTS — handled separately
    ),
    "TrtmntAgent-Other": (
        """CALL {
  MATCH (t:treatment_chemotherapy)-[:of_treatment_chemotherapy]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.chemotherapy_agent, [])
  RETURN p, s
  UNION
  MATCH (t:treatment_radiation)-[:of_treatment_radiation]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.radiation_therapy_type, [])
  RETURN p, s
  UNION
  MATCH (t:treatment_surgery)-[:of_treatment_surgery]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.surgery_type, [])
  RETURN p, s
  UNION
  MATCH (t:treatment_other)-[:of_treatment_other]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.other_treatment_type, [])
  RETURN p, s
}
WITH DISTINCT p, s""",
        """CALL {
  MATCH (t:treatment_chemotherapy)-[:of_treatment_chemotherapy]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.chemotherapy_agent, [])
  RETURN s
  UNION
  MATCH (t:treatment_radiation)-[:of_treatment_radiation]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.radiation_therapy_type, [])
  RETURN s
  UNION
  MATCH (t:treatment_surgery)-[:of_treatment_surgery]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.surgery_type, [])
  RETURN s
  UNION
  MATCH (t:treatment_other)-[:of_treatment_other]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE s.dbgap_accession = 'phs002504'
    AND 'Other' IN coalesce(t.other_treatment_type, [])
  RETURN s
}
WITH DISTINCT s""",
        None,
    ),
    "Response-StableDisease": (
        """MATCH (tr:treatment_response)-[:of_treatment_response]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Stable Disease' IN coalesce(tr.response, [])
WITH DISTINCT p, s""",
        """MATCH (tr:treatment_response)-[:of_treatment_response]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Stable Disease' IN coalesce(tr.response, [])
WITH DISTINCT s""",
        "  AND EXISTS { MATCH (tr:treatment_response)-[:of_treatment_response]->(p) WHERE 'Stable Disease' IN coalesce(tr.response, []) }",
    ),
    "RespCategory-Unknown": (
        """MATCH (tr:treatment_response)-[:of_treatment_response]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Unknown' IN coalesce(tr.response_category, [])
WITH DISTINCT p, s""",
        """MATCH (tr:treatment_response)-[:of_treatment_response]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = 'phs002504'
  AND 'Unknown' IN coalesce(tr.response_category, [])
WITH DISTINCT s""",
        "  AND EXISTS { MATCH (tr:treatment_response)-[:of_treatment_response]->(p) WHERE 'Unknown' IN coalesce(tr.response_category, []) }",
    ),
}

TREATMENT_OR_EXISTS = re.compile(
    r"  AND \(EXISTS \{\s*"
    r"MATCH \(t:treatment_chemotherapy\).*?"
    r"OR EXISTS \{\s*"
    r"MATCH \(t:treatment_other\).*?"
    r"\}\)",
    re.DOTALL,
)

STAT_PREFIX = re.compile(
    r"MATCH \(s:study\)\n"
    r"WHERE s\.dbgap_accession = 'phs002504'\n"
    r"MATCH \(p:participant\)-\[:of_participant\]->\(:consent_group\)-\[:of_consent_group\]->\(s\)\n"
    r"WHERE s\.dbgap_accession = 'phs002504'\n",
    re.MULTILINE,
)

PART_PREFIX = (
    "MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)\n"
    "WHERE s.dbgap_accession = 'phs002504'\n"
)


def suffix_key(filename: str) -> str | None:
    for key in COHORT_BY_SUFFIX:
        if key in filename:
            return key
    return None


BARE_STAT = re.compile(
    r"MATCH \(s:study\)\n"
    r"WHERE s\.dbgap_accession = 'phs002504'\n"
    r"MATCH \(p:participant\)-\[:of_participant\]->\(:consent_group\)-\[:of_consent_group\]->\(s\)\n"
    r"WHERE s\.dbgap_accession = 'phs002504'\n\n"
    r"WITH DISTINCT p, s\n",
    re.MULTILINE,
)

DIAG_EXISTS_IN_TREATMENT = re.compile(
    r" AND EXISTS \{ MATCH \(d:diagnosis\)-\[:of_diagnosis\]->\(p\) WHERE .+? \}",
)
TR_EXISTS_IN_TREATMENT = re.compile(
    r" AND EXISTS \{ MATCH \(tr:treatment_response\)-\[:of_treatment_response\]->\(p\) WHERE .+? \}",
)


def fix_treatment_tab(q: str, cohort_ps: str) -> str:
    if not DIAG_EXISTS_IN_TREATMENT.search(q) and not TR_EXISTS_IN_TREATMENT.search(q):
        return q
    body = q
    body = DIAG_EXISTS_IN_TREATMENT.sub("", body)
    body = TR_EXISTS_IN_TREATMENT.sub("", body)
    if not body.startswith("CALL {"):
        return cohort_ps + "\n" + body
    inner = body[len("CALL {") :]
    inner = re.sub(
        r"^\s*MATCH \(t:",
        "  WITH p, s\n  MATCH (t:",
        inner,
        count=1,
        flags=re.MULTILINE,
    )
    inner = re.sub(
        r"\n  UNION\n  MATCH \(t:",
        "\n  UNION\n  WITH p, s\n  MATCH (t:",
        inner,
    )
    return cohort_ps + "\nCALL {" + inner


def patch_query(
    q: str,
    cohort_ps: str,
    cohort_s: str,
    exists_simple: str | None,
    tab_name: str | None = None,
) -> str:
    if not q or "phs002504" not in q:
        return q
    out = q
    out = re.sub(r"WITH DISTINCT p, s\nWITH DISTINCT p, s\n", "WITH DISTINCT p, s\n", out)
    if BARE_STAT.search(out):
        out = BARE_STAT.sub(cohort_ps + "\n", out, count=1)
    if tab_name == "ParticipantsTab" and out.startswith(PART_PREFIX):
        tail = out[len(PART_PREFIX) :].lstrip("\n")
        if not tail.startswith("MATCH (d:") and not tail.startswith("MATCH (tr:"):
            out = cohort_ps + "\n\n" + tail
    if tab_name == "FilesTab" and out.startswith(PART_PREFIX):
        tail = out[len(PART_PREFIX) :].lstrip("\n")
        if tail.startswith("MATCH (sm:sample)"):
            out = cohort_ps + "\n" + tail
    if tab_name == "TreatmentTab":
        return fix_treatment_tab(out, cohort_ps)
    if TREATMENT_OR_EXISTS.search(out):
        out = TREATMENT_OR_EXISTS.sub(cohort_ps, out, count=1)
    if exists_simple and exists_simple in out:
        out = out.replace(exists_simple, "", 1)
    # StatQuery: study + all participants + EXISTS
    if STAT_PREFIX.search(out) and ("EXISTS" in out or "OR EXISTS" in out):
        out = STAT_PREFIX.sub(cohort_ps + "\n", out, count=1)
        out = out.replace(exists_simple or "", "", 1)
        out = re.sub(r"  AND \(EXISTS[\s\S]*?\)\)\n", "", out, count=1)
    if out.startswith(PART_PREFIX) and ("EXISTS" in out or "OR EXISTS" in out):
        rest = out[len(PART_PREFIX) :]
        rest = re.sub(r"  AND \(EXISTS[\s\S]*?\)\)\n?", "", rest, count=1)
        if exists_simple:
            rest = rest.replace(exists_simple, "", 1)
        out = cohort_ps + "\n" + rest.lstrip("\n")
    # Studies tab outer EXISTS (diagnosis / treatment_response paths)
    studies_pat = re.compile(
        r"MATCH \(s:study\)\nWHERE EXISTS \{\n  MATCH \(d:diagnosis\)-\[:of_diagnosis\]->\(p:participant\)"
        r"-\[:of_participant\]->\(:consent_group\)-\[:of_consent_group\]->\(s\)\n  WHERE s\.dbgap_accession = 'phs002504' AND[^\n]+\n\}\nWITH s",
        re.MULTILINE,
    )
    if studies_pat.search(out):
        out = studies_pat.sub(cohort_s + "\n", out, count=1)
    studies_tr = re.compile(
        r"MATCH \(s:study\)\nWHERE EXISTS \{\n  MATCH \(tr:treatment_response\)-\[:of_treatment_response\]->\(p:participant\)"
        r"-\[:of_participant\]->\(:consent_group\)-\[:of_consent_group\]->\(s\)\n  WHERE s\.dbgap_accession = 'phs002504' AND[^\n]+\n\}\nWITH s",
        re.MULTILINE,
    )
    if studies_tr.search(out):
        out = studies_tr.sub(cohort_s + "\n", out, count=1)
    studies_chemo = re.compile(
        r"MATCH \(s:study\)\nWHERE \(EXISTS \{\n  MATCH \(t:treatment_chemotherapy\)[\s\S]*?\}\)\nWITH s",
        re.MULTILINE,
    )
    if studies_chemo.search(out):
        out = studies_chemo.sub(cohort_s + "\n", out, count=1)
    # Anchored tabs: strip trailing EXISTS after entity MATCH
    if exists_simple and exists_simple in out:
        out = out.replace(exists_simple, "", 1)
    # Survival / samples: replace participant-wide match + EXISTS
    m = re.match(
        r"MATCH \((\w+):(\w+)\)-\[:of_\w+\]->\(p:participant\)-\[:of_participant\]->\(:consent_group\)-\[:of_consent_group\]->\(s:study\)\n"
        r"WHERE s\.dbgap_accession = 'phs002504'\n"
        r"(?:  AND EXISTS \{[^}]+\}\n)?",
        out,
    )
    if m and exists_simple and exists_simple.strip() in q:
        var, label = m.group(1), m.group(2)
        rel = {
            "sv": "survival",
            "sm": "sample",
            "g": "genetic_analysis",
            "tr": "treatment_response",
        }.get(var, label.replace("_", " "))
        if var == "sv":
            rel = "survival"
        elif var == "sm":
            rel = "sample"
        elif var == "g":
            rel = "genetic_analysis"
        elif var == "tr":
            rel = "treatment_response"
        tail = out[m.end() :]
        out = cohort_ps + f"\nMATCH ({var}:{label})-[:of_{rel}]->(p)\n" + tail.lstrip("\n")
    return out


TREATMENT_TAB_GARBAGE = re.compile(
    r"WITH DISTINCT p, s\nMATCH \(d:diagnosis\)-\[:of_diagnosis\]->\(p\)\n  AND .+\nWITH DISTINCT p, s\n",
    re.MULTILINE,
)
TREATMENT_TAB_GARBAGE_TR = re.compile(
    r"WITH DISTINCT p, s\nMATCH \(tr:treatment_response\)-\[:of_treatment_response\]->\(p\)\n  AND .+\nWITH DISTINCT p, s\n",
    re.MULTILINE,
)
REDUNDANT_TREATMENT_STAT = re.compile(
    r"MATCH \(s:study\)\nWHERE s\.dbgap_accession = 'phs002504'\n"
    r"MATCH \(p:participant\)-\[:of_participant\]->\(:consent_group\)-\[:of_consent_group\]->\(s\)\n"
    r"WHERE s\.dbgap_accession = 'phs002504'\n"
    r"(?=MATCH \(t:treatment_chemotherapy\))",
    re.MULTILINE,
)


def scrub_query(q: str, cohort_ps: str) -> str:
    if not q:
        return q
    out = q
    out = TREATMENT_TAB_GARBAGE.sub("WITH DISTINCT p, s\n", out)
    out = TREATMENT_TAB_GARBAGE_TR.sub("WITH DISTINCT p, s\n", out)
    out = out.replace("CALL {  WITH p, s", "CALL {\n  WITH p, s")
    if REDUNDANT_TREATMENT_STAT.search(out):
        out = REDUNDANT_TREATMENT_STAT.sub("", out, count=1)
    return out


def main() -> None:
    paths = sorted(glob.glob(str(BASE / "TC*_C3DC_phs002504*.xlsx")))
    for path in paths:
        key = suffix_key(Path(path).name)
        if not key:
            continue
        cohort_ps, cohort_s, exists_simple = COHORT_BY_SUFFIX[key]
        wb = openpyxl.load_workbook(path)
        ws = wb.active
        headers = [c.value for c in ws[1]]
        tq_i = headers.index("TabQuery")
        sq_i = headers.index("StatQuery")
        changed = False
        for row in ws.iter_rows(min_row=2):
            tab_name = row[headers.index("TabName")].value
            for col in (tq_i, sq_i):
                old = row[col].value
                if not old:
                    continue
                if col == tq_i:
                    new = patch_query(
                        old, cohort_ps, cohort_s, exists_simple, tab_name=tab_name
                    )
                else:
                    new = patch_query(
                        old, cohort_ps, cohort_s, exists_simple, tab_name=None
                    )
                new = scrub_query(new, cohort_ps)
                if new != old:
                    row[col].value = new
                    changed = True
        if changed:
            wb.save(path)
            print("patched", Path(path).name)
        wb.close()


if __name__ == "__main__":
    main()
