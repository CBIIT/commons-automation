"""Rewrite phs000467 C3DC query workbooks to cohort-first Cypher (no EXISTS on entity tabs)."""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl

from Commons.query_reader import read_query_file

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "InputFiles" / "C3DC"
PHS = "phs000467"

# Dynamic stat bar Files (phs002504-style — no nested CALL; distinct dcf_indexd_guid).
STAT_FILE_TAIL = """
OPTIONAL MATCH (sm:sample)-[:of_sample]->(p)
WITH collect(DISTINCT s) AS study_nodes,
     collect(DISTINCT p) AS part_nodes,
     collect(DISTINCT sm) AS sample_nodes
WITH size(study_nodes) AS studies,
     size(part_nodes) AS participants,
     size([sm IN sample_nodes WHERE sm IS NOT NULL]) AS samples,
     part_nodes,
     [sm IN sample_nodes WHERE sm IS NOT NULL] AS sms
UNWIND CASE WHEN size(sms) = 0 THEN [null] ELSE sms END AS sm
OPTIONAL MATCH (f)-[:of_sequencing_file|of_clinical_measure_file|of_cytogenomic_file|of_generic_file|of_methylation_array_file|of_pathology_file|of_radiology_file]->(sm)
WITH studies, participants, samples, part_nodes, collect(DISTINCT f.dcf_indexd_guid) AS s_guids
UNWIND part_nodes AS p
OPTIONAL MATCH (fp)-[:of_clinical_measure_file|of_generic_file|of_radiology_file]->(p)
WITH studies, participants, samples, s_guids, collect(DISTINCT fp.dcf_indexd_guid) AS p_guids
WITH studies, participants, samples, [g IN s_guids + p_guids WHERE g IS NOT NULL] AS guids
UNWIND CASE WHEN size(guids) = 0 THEN [null] ELSE guids END AS guid
RETURN studies, participants, samples, count(DISTINCT guid) AS files"""


def _parse_cohort(qf) -> tuple[str, str]:
    """Return (anchor, predicate) where anchor is participant|diagnosis|survival."""
    diag = qf.query_for_tab("DiagnosisTab")
    m = re.search(
        r"WHERE s\.dbgap_accession = 'phs000467'\s*\n((?:  AND .+\n)*)",
        diag,
    )
    if not m:
        raise ValueError(f"No cohort WHERE block in DiagnosisTab for {qf.path.name}")
    preds = [
        ln.strip()[4:]
        for ln in m.group(1).splitlines()
        if ln.strip().startswith("AND ")
    ]
    pred = "\n  AND ".join(preds)
    head = diag.lstrip()[:80]
    if head.startswith("MATCH (sv:survival)"):
        return "survival", pred
    if head.startswith("MATCH (p:participant)"):
        return "participant", pred
    if head.startswith("MATCH (d:diagnosis)"):
        if any("p." in p or "coalesce(p." in p for p in preds):
            return "participant", pred
        return "diagnosis", pred
    raise ValueError(f"Unknown DiagnosisTab anchor in {qf.path.name}")


def _cohort_ps(anchor: str, pred: str) -> str:
    if anchor == "participant":
        return (
            f"MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)\n"
            f"WHERE s.dbgap_accession = '{PHS}'\n"
            f"  AND {pred}\n"
            f"WITH DISTINCT p, s"
        )
    if anchor == "diagnosis":
        return (
            f"MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->"
            f"(:consent_group)-[:of_consent_group]->(s:study)\n"
            f"WHERE s.dbgap_accession = '{PHS}'\n"
            f"  AND {pred}\n"
            f"WITH DISTINCT p, s"
        )
    return (
        f"MATCH (sv:survival)-[:of_survival]->(p:participant)-[:of_participant]->"
        f"(:consent_group)-[:of_consent_group]->(s:study)\n"
        f"WHERE s.dbgap_accession = '{PHS}'\n"
        f"  AND {pred}\n"
        f"WITH DISTINCT p, s"
    )


def _cohort_s(anchor: str, pred: str) -> str:
    if anchor == "participant":
        return (
            f"MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)\n"
            f"WHERE s.dbgap_accession = '{PHS}' AND {pred}\n"
            f"WITH DISTINCT s"
        )
    if anchor == "diagnosis":
        return (
            f"MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->"
            f"(:consent_group)-[:of_consent_group]->(s:study)\n"
            f"WHERE s.dbgap_accession = '{PHS}' AND {pred}\n"
            f"WITH DISTINCT s"
        )
    return (
        f"MATCH (sv:survival)-[:of_survival]->(p:participant)-[:of_participant]->"
        f"(:consent_group)-[:of_consent_group]->(s:study)\n"
        f"WHERE s.dbgap_accession = '{PHS}' AND {pred}\n"
        f"WITH DISTINCT s"
    )


def _stat_query(anchor: str, pred: str) -> str:
    """Study-first cohort + dynamic Files count (aligned with phs002504 StatQuery)."""
    if anchor == "diagnosis":
        head = (
            f"MATCH (s:study)\n"
            f"WHERE s.dbgap_accession = '{PHS}'\n"
            f"MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->"
            f"(:consent_group)-[:of_consent_group]->(s)\n"
            f"WHERE {pred}\n"
            f"WITH DISTINCT p, s\n"
        )
    elif anchor == "participant":
        head = (
            f"MATCH (s:study)\n"
            f"WHERE s.dbgap_accession = '{PHS}'\n"
            f"MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s)\n"
            f"WHERE {pred}\n"
            f"WITH DISTINCT p, s\n"
        )
    else:
        head = (
            f"MATCH (s:study)\n"
            f"WHERE s.dbgap_accession = '{PHS}'\n"
            f"MATCH (sv:survival)-[:of_survival]->(p:participant)-[:of_participant]->"
            f"(:consent_group)-[:of_consent_group]->(s)\n"
            f"WHERE {pred}\n"
            f"WITH DISTINCT p, s\n"
        )
    return head + STAT_FILE_TAIL + "\n"


EXISTS_D = re.compile(
    r"\s*AND EXISTS \{ MATCH \(d:diagnosis\)-\[:of_diagnosis\]->\(p\) WHERE .+? \}",
    re.DOTALL,
)
EXISTS_SV = re.compile(
    r"\s*AND EXISTS \{ MATCH \(sv:survival\)-\[:of_survival\]->\(p\) WHERE .+? \}",
    re.DOTALL,
)


def _rewrite_tab(tab: str, q: str, anchor: str, pred: str, cohort_ps: str, cohort_s: str) -> str:
    if tab == "DiagnosisTab":
        return q

    if tab == "StudiesTab":
        m = re.search(r"WHERE EXISTS \{[\s\S]+?\}\nWITH s\n", q)
        if not m:
            return q
        body = q[m.end() :]
        return f"{cohort_s}\nWITH s\n{body}"

    if tab == "ParticipantsTab":
        if EXISTS_D.search(q):
            ret = q.split("RETURN", 1)[1]
            return f"{cohort_ps}\nRETURN{ret}"
        if anchor == "survival" and "WITH DISTINCT p, s" in q.split("RETURN")[0]:
            return q
        if anchor == "participant" and not EXISTS_D.search(q):
            return q
        return q

    if tab == "SurvivalTab":
        if anchor == "survival":
            return q
        if EXISTS_D.search(q):
            ret = q.split("RETURN", 1)[1]
            return f"{cohort_ps}\nMATCH (sv:survival)-[:of_survival]->(p)\nRETURN{ret}"
        if q.startswith("MATCH (sv:survival)"):
            ret = q.split("RETURN", 1)[1]
            return f"{cohort_ps}\nMATCH (sv:survival)-[:of_survival]->(p)\nRETURN{ret}"
        return q

    if tab == "TreatmentTab":
        if not EXISTS_D.search(q) and not EXISTS_SV.search(q):
            return q
        indent = "  "
        cohort_block = "\n".join(indent + line for line in cohort_ps.split("\n"))
        chunks = q.split("CALL {")
        out = chunks[0]
        for chunk in chunks[1:]:
            chunk = EXISTS_D.sub("", chunk)
            chunk = EXISTS_SV.sub("", chunk)
            chunk = re.sub(
                rf"WHERE s\.dbgap_accession = '{PHS}'\s*\n",
                "",
                chunk,
                count=1,
            )
            out += "CALL {\n" + cohort_block + "\n" + chunk.lstrip("\n")
        return out

    # Generic entity tabs + FilesTab
    if EXISTS_D.search(q) or EXISTS_SV.search(q):
        q2 = EXISTS_D.sub("", q)
        q2 = EXISTS_SV.sub("", q2)
        parts = q2.split("RETURN", 1)
        if len(parts) != 2:
            return q
        head, ret = parts[0], parts[1]
        head = head.replace(f"WHERE s.dbgap_accession = '{PHS}'\n", "")
        head = head.replace(f"WHERE s.dbgap_accession = '{PHS}'", "")
        head = head.strip()
        if head.startswith("MATCH (p:participant)"):
            lines = head.split("\n")
            head = "\n".join(lines[1:]).strip()
        return f"{cohort_ps}\n{head}\nRETURN{ret}"

    return q


def patch_workbook(path: Path) -> list[str]:
    qf = read_query_file("C3DC", path.name)
    anchor, pred = _parse_cohort(qf)
    cohort_ps = _cohort_ps(anchor, pred)
    cohort_s = _cohort_s(anchor, pred)
    stat = _stat_query(anchor, pred)

    wb = openpyxl.load_workbook(path)
    ws = wb.active
    changed: list[str] = []
    for row in ws.iter_rows(min_row=2):
        tab = row[0].value
        if not tab:
            continue
        old = row[1].value
        if old is None:
            continue
        old_s = str(old)
        new_s = _rewrite_tab(str(tab), old_s, anchor, pred, cohort_ps, cohort_s)
        if new_s != old_s:
            row[1].value = new_s
            changed.append(str(tab))
        if tab == "ParticipantsTab" and len(row) > 2:
            if row[2].value is None or str(row[2].value) != stat:
                row[2].value = stat
                if "StatQuery" not in changed:
                    changed.append("StatQuery")

    if changed:
        wb.save(path)
    wb.close()
    return changed


def main() -> None:
    paths = sorted(IN.glob(f"*_C3DC_{PHS}_*.xlsx"))
    if not paths:
        raise SystemExit(f"No workbooks for {PHS}")
    for path in paths:
        changed = patch_workbook(path)
        print(f"{path.name}: {', '.join(changed) if changed else 'no changes'}")


if __name__ == "__main__":
    main()
