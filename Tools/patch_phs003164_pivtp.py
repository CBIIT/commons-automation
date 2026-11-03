"""Align phs003164 (PIVTP Leukemia) C3DC workbooks with Explore PDX/sample diagnosis behavior."""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl

from Commons.query_reader import read_query_file

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "InputFiles" / "C3DC"
PHS = "phs003164"

FILES_ROLLUP = """
WITH size(study_nodes) AS studies,
     size(part_nodes) AS participants,
     size(sample_nodes) AS samples,
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

OLD_STUDIES_SAMPLES = (
    "OPTIONAL MATCH (sm:sample)-[:of_sample]->(:participant)-[:of_participant]->"
    "(:consent_group)-[:of_consent_group]->(s)\n"
    "WITH s, num_of_participants, count(DISTINCT sm) AS num_of_samples"
)

NEW_STUDIES_SAMPLES = """OPTIONAL MATCH (s)<-[*..2]-(pcp)<-[:of_sample]-(sm1:sample)
WHERE pcp:participant OR pcp:cell_line OR pcp:pdx
WITH s, num_of_participants, count(DISTINCT sm1.sample_id) AS num_samples_1
OPTIONAL MATCH (s)<-[:of_consent_group]-(:consent_group)<-[:of_participant]-(:participant)<-[:of_sample]-(:sample)<--(cp)<--(sm2:sample)
WHERE cp:cell_line OR cp:pdx
WITH s, num_of_participants, num_samples_1 + count(DISTINCT sm2.sample_id) AS num_of_samples"""

OLD_DIAG_TOP5 = (
    "OPTIONAL MATCH (d:diagnosis)-[:of_diagnosis]->(dp:participant)-[:of_participant]->"
    "(:consent_group)-[:of_consent_group]->(s)\n"
    "WITH s, num_of_participants, num_of_samples, d.diagnosis AS diagnosis_name, count(DISTINCT dp) AS diagnosis_n"
)

NEW_DIAG_TOP5 = """OPTIONAL MATCH (s)<-[*..6]-(dg:diagnosis)
WITH s, num_of_participants, num_of_samples, dg.diagnosis AS diagnosis_name, count(dg) AS diagnosis_n"""


def _participants_where_body(participants_tab: str) -> str:
    m = re.search(
        rf"WHERE\s+(s\.dbgap_accession\s*=\s*'{PHS}'\s*\n(?:\s*AND[^\n]+\n)*)",
        participants_tab,
    )
    if not m:
        raise ValueError("Could not parse ParticipantsTab WHERE block")
    return m.group(1).strip()


def make_stat(where_body: str) -> str:
    return f"""MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE {where_body}
WITH collect(DISTINCT s) AS study_nodes, collect(DISTINCT p) AS part_nodes
CALL {{
  WITH part_nodes
  UNWIND part_nodes AS p
  MATCH (sm:sample)-[:of_sample]->(p)
  RETURN sm
  UNION
  WITH part_nodes
  UNWIND part_nodes AS p
  MATCH (parent:sample)-[:of_sample]->(p)
  MATCH (sm:sample)-[:of_sample]->(:cell_line)-[:of_cell_line]->(parent)
  RETURN sm
  UNION
  WITH part_nodes
  UNWIND part_nodes AS p
  MATCH (parent:sample)-[:of_sample]->(p)
  MATCH (sm:sample)-[:of_sample]->(:pdx)-[:of_pdx]->(parent)
  RETURN sm
}}
WITH study_nodes, part_nodes, collect(DISTINCT sm) AS sample_nodes{FILES_ROLLUP}"""


def make_samples(where_body: str) -> str:
    return f"""CALL {{
  MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE {where_body}
  WITH DISTINCT p, s
  MATCH (sm:sample)-[:of_sample]->(p)
  WHERE coalesce(sm.sample_tumor_status, '') <> 'Normal'
  MATCH (f)-[:of_sequencing_file|of_clinical_measure_file|of_cytogenomic_file|of_generic_file|of_methylation_array_file|of_pathology_file|of_radiology_file]->(sm)
  RETURN sm, p, s
  UNION
  MATCH (p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE {where_body}
  WITH DISTINCT p, s
  MATCH (parent:sample)-[:of_sample]->(p)
  MATCH (sm:sample)-[:of_sample]->(:pdx)-[:of_pdx]->(parent)
  WHERE coalesce(sm.sample_tumor_status, '') <> 'Normal'
  RETURN sm, p, s
}}
WITH DISTINCT sm, p, s
RETURN p.participant_id AS `Participant ID`,
       sm.sample_id AS `Sample ID`,
       s.study_id AS `Study ID`,
       sm.tumor_spatial_extent AS `Tumor Spatial Extent`,
       reduce(text = '', site IN coalesce(sm.anatomic_site, []) | CASE WHEN text = '' THEN site ELSE text + ';' + site END) AS `Anatomic Site`,
       CASE
         WHEN sm.participant_age_at_collection IS NULL OR sm.participant_age_at_collection = -999 THEN 'Not Reported'
         ELSE toString(sm.participant_age_at_collection)
       END AS `Participant Age at Collection (days)`,
       sm.sample_tumor_status AS `Sample Tumor Status`
ORDER BY p.participant_id, sm.sample_id
LIMIT 100;"""


def make_diagnosis(where_body: str) -> str:
    # where_body uses p.sex_at_birth / EXISTS — reuse in every UNION branch.
    return f"""CALL {{
  MATCH (d:diagnosis)-[:of_diagnosis]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE {where_body}
  RETURN d, p
  UNION
  MATCH (d:diagnosis)-[:of_diagnosis]->(:sample)-[:of_sample]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE {where_body}
  RETURN d, p
  UNION
  MATCH (d:diagnosis)-[:of_diagnosis]->(:sample)-[:of_sample]->(:cell_line)-[:of_cell_line]->(:sample)-[:of_sample]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE {where_body}
  RETURN d, p
  UNION
  MATCH (d:diagnosis)-[:of_diagnosis]->(:sample)-[:of_sample]->(:pdx)-[:of_pdx]->(:sample)-[:of_sample]->(p:participant)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
  WHERE {where_body}
  RETURN d, p
}}
WITH DISTINCT d, p
MATCH (p)-[:of_participant]->(:consent_group)-[:of_consent_group]->(s:study)
WHERE s.dbgap_accession = '{PHS}'
WITH p, s, collect(DISTINCT d) AS ds
WITH p, s, ds, [x IN ds WHERE x.diagnosis_id <> p.participant_id + '.diagnosis'] AS sample_dx
WHERE size(sample_dx) > 0
UNWIND ds AS d
RETURN p.participant_id AS `Participant ID`,
       d.diagnosis_id AS `Diagnosis ID`,
       d.diagnosis AS `Diagnosis`,
       CASE
         WHEN d.age_at_diagnosis IS NULL OR d.age_at_diagnosis = -999 THEN 'Not Reported'
         ELSE toString(d.age_at_diagnosis)
       END AS `Age at Diagnosis (days)`,
       reduce(text = '', value IN coalesce(d.anatomic_site, []) | CASE WHEN text = '' THEN value ELSE text + ', ' + value END) AS `Anatomic Site`,
       reduce(text = '', value IN coalesce(d.diagnosis_classification_system, []) | CASE WHEN text = '' THEN value ELSE text + ', ' + value END) AS `Diagnosis Classification System`,
       s.dbgap_accession AS `dbGaP Accession`
ORDER BY p.participant_id, d.diagnosis_id
LIMIT 100;"""


def patch_studies_tab(q: str) -> str:
    q = q.replace(OLD_STUDIES_SAMPLES, NEW_STUDIES_SAMPLES)
    q = q.replace(OLD_DIAG_TOP5, NEW_DIAG_TOP5)
    q = q.replace("count(DISTINCT d2) AS site_n", "count(d2) AS site_n")
    q = q.replace(
        "ORDER BY type_n DESC\n",
        "ORDER BY type_n DESC, file_type DESC\n",
    )
    return q


def patch_workbook(path: Path) -> None:
    qf = read_query_file("C3DC", path.name)
    where_body = _participants_where_body(qf.query_for_tab("ParticipantsTab"))

    wb = openpyxl.load_workbook(path)
    ws = wb.active
    for row in ws.iter_rows(min_row=2):
        tab = row[0].value
        if tab == "ParticipantsTab":
            row[2].value = make_stat(where_body)
        elif tab == "SamplesTab":
            row[1].value = make_samples(where_body)
        elif tab == "DiagnosisTab":
            row[1].value = make_diagnosis(where_body)
        elif tab == "StudiesTab" and row[1].value:
            row[1].value = patch_studies_tab(row[1].value)
    wb.save(path)
    wb.close()


def main() -> None:
    for path in sorted(IN.glob(f"*_{PHS}_*.xlsx")):
        patch_workbook(path)
        print("patched", path.name)


if __name__ == "__main__":
    main()
