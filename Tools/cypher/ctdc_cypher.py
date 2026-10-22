"""CTDC SQL → Memgraph Cypher for InputFiles workbooks (used by Tools/convert_ctdc_sql_to_cypher.py)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# SQL alias (df_* tables) -> Cypher variable used in templates.
_ALIAS = {
    "std": "study",
    "prt": "sb",
    "demo": "demo",
    "dgn": "dgn",
    "exp": "exp",
    "tgt": "tt",
    "bio": "spec",
    "fil": "f",
}

_FILE_SIZE_EXPR = """
CASE
  WHEN coalesce(f.data_file_size, 0) >= 1024 * 1024 * 1024 THEN
    CASE
      WHEN round(f.data_file_size / (1024.0 * 1024.0 * 1024.0), 2) = toInteger(round(f.data_file_size / (1024.0 * 1024.0 * 1024.0), 0))
      THEN toString(toInteger(round(f.data_file_size / (1024.0 * 1024.0 * 1024.0), 0))) + ' GB'
      ELSE toString(round(f.data_file_size / (1024.0 * 1024.0 * 1024.0), 2)) + ' GB'
    END
  WHEN coalesce(f.data_file_size, 0) >= 1024 * 1024 THEN
    CASE
      WHEN round(f.data_file_size / (1024.0 * 1024.0), 2) = toInteger(round(f.data_file_size / (1024.0 * 1024.0), 0))
      THEN toString(toInteger(round(f.data_file_size / (1024.0 * 1024.0), 0))) + ' MB'
      ELSE toString(round(f.data_file_size / (1024.0 * 1024.0), 2)) + ' MB'
    END
  WHEN coalesce(f.data_file_size, 0) >= 1024 THEN
    CASE
      WHEN round(f.data_file_size / 1024.0, 2) = toInteger(round(f.data_file_size / 1024.0, 0))
      THEN toString(toInteger(round(f.data_file_size / 1024.0, 0))) + ' KB'
      ELSE toString(round(f.data_file_size / 1024.0, 2)) + ' KB'
    END
  ELSE
    CASE
      WHEN round(f.data_file_size, 2) = toInteger(round(f.data_file_size, 0))
      THEN toString(toInteger(round(f.data_file_size, 0))) + ' Bytes'
      ELSE toString(round(f.data_file_size, 2)) + ' Bytes'
    END
END
""".strip()


@dataclass
class SqlFilters:
    """Normalized filter conditions from SQL WHERE."""
    study_id: str = "NCT04314401"
    predicates: Tuple[str, ...] = ()  # Cypher AND fragments (without leading AND)
    require_file_name: bool = False


def _extract_where(sql: str) -> str:
    m = re.search(r"\bWHERE\b(.*)", sql, flags=re.I | re.S)
    if not m:
        return ""
    tail = m.group(1)
    for stop in ("GROUP BY", "ORDER BY", "LIMIT", ";"):
        idx = re.search(rf"\b{stop}\b", tail, flags=re.I)
        if idx:
            tail = tail[: idx.start()]
    return tail.strip()


def _split_and(where: str) -> List[str]:
    parts: List[str] = []
    depth = 0
    quote: Optional[str] = None
    cur: List[str] = []
    for ch in where:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            cur.append(ch)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            continue
        if ch.upper() == "A" and "".join(cur[-3:]).upper() == "":
            pass
        cur.append(ch)
    # split on AND at depth 0
    text = "".join(cur)
    chunk = ""
    depth = 0
    quote = None
    for i, ch in enumerate(text):
        if quote:
            chunk += ch
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            chunk += ch
            continue
        if ch == "(":
            depth += 1
            chunk += ch
            continue
        if ch == ")":
            depth -= 1
            chunk += ch
            continue
        if depth == 0 and text[i : i + 4].upper() == " AND":
            p = chunk.strip()
            if p:
                parts.append(p)
            chunk = ""
            continue
        chunk += ch
    if chunk.strip():
        parts.append(chunk.strip())
    return parts


def _sql_pred_to_cypher(pred: str) -> Optional[str]:
    pred = re.sub(r"\s+", " ", pred.strip())
    if re.match(r"fil\.data_file_name\s+IS\s+NOT\s+NULL", pred, re.I):
        return None
    m = re.match(
        r"(?P<lhs>[a-zA-Z0-9_.\"]+)\s*=\s*'(?P<val>(?:''|[^'])*)'",
        pred,
    )
    if not m:
        return None
    lhs = m.group("lhs").strip()
    val = m.group("val").replace("''", "'")
    if "." not in lhs:
        return None
    alias, prop = lhs.split(".", 1)
    alias = alias.strip('"')
    var = _ALIAS.get(alias)
    if not var:
        return None
    if var == "study" and prop == "study_id":
        return None
    escaped = val.replace("\\", "\\\\").replace("'", "\\'")
    if var == "spec" and prop == "anatomical_collection_site":
        return (
            f"toLower(coalesce({var}.{prop}, '')) = toLower('{escaped}')"
        )
    return f"{var}.{prop} = '{escaped}'"


def parse_sql_filters(sql: str) -> SqlFilters:
    where = _extract_where(sql)
    study_id = "NCT04314401"
    m = re.search(r"std\.study_id\s*=\s*'([^']+)'", where, re.I)
    if m:
        study_id = m.group(1)
    preds: List[str] = []
    require_file = False
    for part in _split_and(where):
        if re.search(r"fil\.data_file_name\s+IS\s+NOT\s+NULL", part, re.I):
            require_file = True
            continue
        c = _sql_pred_to_cypher(part)
        if c:
            preds.append(c)
    return SqlFilters(study_id=study_id, predicates=tuple(preds), require_file_name=require_file)


def _filter_block(f: SqlFilters, *, include_file: bool = False) -> str:
    lines = [f"MATCH (study:study)<-[:belongs_to]-(sb:participant)", f"WHERE study.study_id = '{f.study_id}'"]
    lines += [
        "OPTIONAL MATCH (demo:demographic)-[:of_participant]->(sb)",
        "OPTIONAL MATCH (dgn:diagnosis)-[:of_participant]->(sb)",
        "OPTIONAL MATCH (exp:exposure)-[:of_participant]->(sb)",
        "OPTIONAL MATCH (tt:targeted_therapy)-[:of_participant]->(sb)",
        "OPTIONAL MATCH (spec:specimen)-[:of_participant]->(sb)",
    ]
    if include_file:
        lines.append("OPTIONAL MATCH (f:file)-[:associated_with]-(sb)")
        lines.append("OPTIONAL MATCH (f)-[:associated_with]->(spec)")
    if f.predicates:
        lines.append("WITH study, sb, demo, dgn, exp, tt, spec" + (", f" if include_file else ""))
        lines.append("WHERE " + " AND ".join(f.predicates))
    return "\n".join(lines)


def stat_query(f: SqlFilters) -> str:
    block = _filter_block(f, include_file=True)
    extra = " AND f.data_file_name IS NOT NULL" if f.require_file_name else ""
    return f"""
{block}
WITH study, sb, dgn, tt, spec, f
WHERE true{extra}
RETURN
  count(DISTINCT study.study_id) AS Studies,
  count(DISTINCT sb.participant_id) AS Participants,
  count(DISTINCT dgn.ctep_disease_term) AS Diagnoses,
  count(DISTINCT tt.targeted_therapy) AS `Targeted Therapies`,
  count(DISTINCT spec.specimen_record_id) AS Biospecimens,
  count(DISTINCT f.data_file_uuid) AS Files
""".strip()


def participants_tab_query(f: SqlFilters) -> str:
    block = _filter_block(f)
    return f"""
{block}
WITH study, sb, demo, dgn, exp, tt, spec
CALL {{
  WITH sb
  OPTIONAL MATCH (sb)<-[:of_participant]-(d:diagnosis)
  WITH d ORDER BY coalesce(d.updated, d.created) DESC, id(d) DESC
  RETURN head(collect(d)) AS d_latest
}}
CALL {{
  WITH sb
  OPTIONAL MATCH (sb)<-[:of_participant]-(tt:targeted_therapy)
  WITH [t IN collect(tt.targeted_therapy) WHERE t IS NOT NULL AND trim(toString(t)) <> ''] AS ts
  WITH apoc.coll.toSet(ts) AS dedup
  RETURN CASE WHEN size(dedup) > 0 THEN apoc.text.join(apoc.coll.sort(dedup), '|') ELSE null END AS targeted_therapy_string
}}
RETURN DISTINCT
  sb.participant_id AS `Participant ID`,
  d_latest.ctep_disease_term AS Diagnosis,
  demo.age_at_enrollment AS Age,
  demo.sex AS Sex,
  demo.race AS Race,
  demo.ethnicity AS Ethnicity,
  coalesce(exp.carcinogen_exposure, '') AS `Carcinogen Exposure`,
  replace(targeted_therapy_string, '|', ', ') AS `Targeted Therapy`
ORDER BY sb.participant_id
LIMIT 100
""".strip()


def biospecimens_tab_query(f: SqlFilters) -> str:
    block = _filter_block(f)
    return f"""
{block}
WITH study, sb, dgn, spec, demo, exp
WHERE spec.specimen_record_id IS NOT NULL
CALL {{
  WITH sb
  OPTIONAL MATCH (sb)<-[:of_participant]-(d:diagnosis)
  WITH d ORDER BY id(d) DESC
  RETURN head(collect(d)) AS d_latest
}}
RETURN DISTINCT
  sb.participant_id AS `Participant ID`,
  d_latest.ctep_disease_term AS Diagnosis,
  apoc.text.capitalizeAll(toLower(coalesce(d_latest.primary_disease_site, ''))) AS `Primary Site`,
  spec.specimen_record_id AS `Specimen Record ID`,
  apoc.text.capitalizeAll(toLower(coalesce(spec.anatomical_collection_site, ''))) AS `Anatomical Collection Site`,
  spec.tissue_category AS `Tissue Category`,
  spec.assessment_timepoint AS `Collection Timepoint`
ORDER BY spec.specimen_record_id
LIMIT 100
""".strip()


def _files_tab_query(f: SqlFilters, *, association: str) -> str:
    """association: 'data' (participant/biospecimen) or 'study'."""
    preds = list(f.predicates)
    pred_sql = (" AND " + " AND ".join(preds)) if preds else ""
    study_only = association == "study"
    assoc_filter = (
        "size(associations) = 1 AND 'study' IN associations"
        if study_only
        else "('biospecimen' IN associations OR 'participant' IN associations)"
    )
    return f"""
MATCH (f:file)
CALL {{
  WITH f
  MATCH (f)-[:associated_with]-(s:study)
  WHERE NOT (f)-[:associated_with]-(:participant) AND NOT (f)-[:associated_with]-(:specimen)
  RETURN f.data_file_uuid AS uuid, 'study' AS association
  UNION
  WITH f
  MATCH (f)-[:associated_with]-(:participant)
  WHERE NOT (f)-[:associated_with]-(:specimen)
  RETURN f.data_file_uuid AS uuid, 'participant' AS association
  UNION
  WITH f
  MATCH (f)-[:associated_with]-(:specimen)-[:of_participant]->(:participant)
  RETURN f.data_file_uuid AS uuid, 'biospecimen' AS association
}}
WITH f, apoc.coll.toSet(collect(DISTINCT association)) AS associations
WHERE {assoc_filter}
MATCH (study:study)-[:associated_with]-(f)
WHERE study.study_id = '{f.study_id}'
OPTIONAL MATCH (f)-[:associated_with]->(spec1:specimen)-[:of_participant]->(sb:participant)<-[:belongs_to]-(study)
OPTIONAL MATCH (f)-[:associated_with]->(sb2:participant)<-[:belongs_to]-(study)
WITH f, study, coalesce(sb, sb2) AS sb, spec1 AS spec
OPTIONAL MATCH (demo:demographic)-[:of_participant]->(sb)
OPTIONAL MATCH (dgn:diagnosis)-[:of_participant]->(sb)
OPTIONAL MATCH (exp:exposure)-[:of_participant]->(sb)
OPTIONAL MATCH (tt:targeted_therapy)-[:of_participant]->(sb)
WHERE sb IS NOT NULL{pred_sql}
RETURN DISTINCT
  study.study_accession AS `Study Accession`,
  f.data_file_name AS `File Name`,
  f.data_file_format AS Format,
  f.data_file_type AS `File Type`,
  {_FILE_SIZE_EXPR} AS Size,
  f.data_file_description AS Description,
  coalesce(spec.specimen_record_id, '') AS `Specimen Record ID`,
  coalesce(sb.participant_id, '') AS `Participant ID`,
  head(collect(dgn.ctep_disease_term)) AS Diagnosis
ORDER BY f.data_file_name
LIMIT 100
""".strip()


def files_tab_query(f: SqlFilters) -> str:
    return _files_tab_query(f, association="data")


def study_files_tab_query(f: SqlFilters) -> str:
    q = _files_tab_query(f, association="study")
    # Study Files tab columns (no participant/specimen/diagnosis columns in UI).
    return q.replace(
        """  coalesce(spec.specimen_record_id, '') AS `Specimen Record ID`,
  coalesce(sb.participant_id, '') AS `Participant ID`,
  head(collect(dgn.ctep_disease_term)) AS Diagnosis""",
        "",
    ).replace(",\n\nORDER BY", "\nORDER BY")


def queries_from_sql(stat_sql: str, participants_sql: str) -> Dict[str, str]:
    f = parse_sql_filters(stat_sql or participants_sql)
    if participants_sql:
        f = parse_sql_filters(participants_sql)
    return {
        "StatQuery": stat_query(f),
        "ParticipantsTab": participants_tab_query(f),
        "BiospecimensTab": biospecimens_tab_query(f),
        "FilesTab": files_tab_query(f),
        "StudyFilesTab": study_files_tab_query(f),
    }
