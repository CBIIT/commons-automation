"""Build Neo4j Cypher for ICDC explore tests from legacy Katalon SQL in input workbooks."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# SQL alias.column -> cypher (var, prop, mode)
_COL_MAP = {
    ("st", "clinical_study_designation"): ("s", "clinical_study_designation", "eq"),
    ("st", "clinical_study_type"): ("s", "clinical_study_type", "eq"),
    ("dmg", "breed"): ("demo", "breed", "eq"),
    ("diag", "disease_term"): ("diag", "disease_term", "eq"),
    ("diag", "primary_disease_site"): ("diag", "primary_disease_site", "eq"),
    ("diag", "stage_of_disease"): ("diag", "stage_of_disease", "eq"),
    ("diag", "best_response"): ("diag", "best_response", "eq"),
    ("reg", "registration_origin"): ("__biobank__", "registration_origin", "eq"),
}


def _cq(val: str) -> str:
    return "'" + val.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _extract_sql_string(sql: str, open_quote_idx: int) -> tuple[str, int]:
    i = open_quote_idx + 1
    while i < len(sql):
        if sql[i] == "'":
            if i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            rest = sql[i + 1 :].lstrip()
            if rest == "" or rest.upper().startswith(("AND", "GROUP", "ORDER", "LIMIT", ")", ";", ",")):
                return sql[open_quote_idx + 1 : i].replace("''", "'"), i + 1
        i += 1
    raise ValueError("unclosed SQL string")


def parse_sql_filters(sql: str) -> List[Tuple[str, str, str]]:
    out: List[Tuple[str, str, str]] = []
    for m in re.finditer(r"(?:^|[\s(])([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*=\s*'", sql, re.I):
        open_q = m.end() - 1
        try:
            val, _ = _extract_sql_string(sql, open_q)
        except ValueError:
            continue
        out.append((m.group(1), m.group(2), val))
    return out


@dataclass
class IcdcFilters:
    study_code: str = ""
    predicates: List[Tuple[str, str, str, str]] = field(default_factory=list)  # var, prop, val, mode

    @classmethod
    def from_cases_sql(cls, sql: str) -> "IcdcFilters":
        raw = parse_sql_filters(sql)
        study = ""
        preds: List[Tuple[str, str, str, str]] = []
        for alias, col, val in raw:
            if (alias, col) not in _COL_MAP:
                continue
            var, prop, mode = _COL_MAP[(alias, col)]
            if var == "s" and prop == "clinical_study_designation":
                study = val
                continue
            preds.append((var, prop, val, mode))
        if not study:
            for alias, col, val in raw:
                if alias == "st" and col == "clinical_study_designation":
                    study = val
        return cls(study_code=study, predicates=preds)


def _biobank_clause(val: str) -> str:
    if val == "Not Applicable":
        return """
NOT EXISTS {
  MATCH (r:registration)-[:of_case]->(c)
  WHERE r.registration_origin IS NOT NULL AND r.registration_origin <> s.clinical_study_designation
}""".strip()
    return f"""
EXISTS {{
  MATCH (r:registration)-[:of_case]->(c)
  WHERE r.registration_origin = {_cq(val)}
}}""".strip()


def _where_extra(f: IcdcFilters) -> str:
    parts: List[str] = []
    for var, prop, val, mode in f.predicates:
        if var == "__biobank__":
            parts.append(_biobank_clause(val))
            continue
        if mode == "eq":
            parts.append(f"{var}.{prop} = {_cq(val)}")
    if not parts:
        return ""
    return "WHERE " + "\n  AND ".join(parts)


def _core_case_filter(f: IcdcFilters) -> str:
    """Tight graph pattern (member_of / of_case) — avoids `[*]` path explosion in counts."""
    extra = _where_extra(f)
    return f"""
MATCH (s:study {{clinical_study_designation: {_cq(f.study_code)}}})
MATCH (c:case)-[:member_of]->(s)
MATCH (p:program)<-[:member_of]-(s)
MATCH (demo:demographic)-[:of_case]->(c)
MATCH (diag:diagnosis)-[:of_case]->(c)
{extra}""".strip()


_AGE = """
CASE
  WHEN demo.patient_age_at_enrollment IS NULL THEN ''
  WHEN demo.patient_age_at_enrollment = toInteger(demo.patient_age_at_enrollment)
    THEN toString(toInteger(demo.patient_age_at_enrollment))
  ELSE toString(demo.patient_age_at_enrollment)
END""".strip()

_WEIGHT = """
CASE
  WHEN demo.weight IS NULL THEN ''
  WHEN demo.weight = toInteger(demo.weight) THEN toString(toInteger(round(demo.weight)))
  ELSE toString(demo.weight)
END""".strip()

_FORMAT_FROM_NAME = """
CASE
  WHEN name ENDS WITH '.bai' THEN 'bai'
  WHEN name ENDS WITH '.bam' THEN 'bam'
  WHEN name ENDS WITH '.csv' THEN 'csv'
  WHEN name ENDS WITH '.doc' THEN 'doc'
  WHEN name ENDS WITH '.docx' THEN 'docx'
  WHEN name ENDS WITH '.fastq.gz' THEN 'fastq'
  WHEN name ENDS WITH '.vcf.gz' THEN 'vcf'
  WHEN name ENDS WITH '.tsv.gz' THEN 'tsv'
  WHEN name ENDS WITH '.pdf' THEN 'pdf'
  WHEN name ENDS WITH '.rtf' THEN 'rtf'
  WHEN name ENDS WITH '.tbi' THEN 'tbi'
  WHEN name ENDS WITH '.tif' THEN 'tif'
  WHEN name ENDS WITH '.xls' THEN 'xls'
  WHEN name ENDS WITH '.xlsx' THEN 'xlsx'
  ELSE 'Unknown'
END""".strip()

_FORMAT_STUDY = """
CASE
  WHEN name ENDS WITH '.bai' THEN 'bai'
  WHEN name ENDS WITH '.bam' THEN 'bam'
  WHEN name ENDS WITH '.csv' THEN 'csv'
  WHEN name ENDS WITH '.doc' THEN 'doc'
  WHEN name ENDS WITH '.docx' THEN 'docx'
  WHEN name ENDS WITH '.gz' THEN 'gz'
  WHEN name ENDS WITH '.pdf' THEN 'pdf'
  WHEN name ENDS WITH '.rtf' THEN 'rtf'
  WHEN name ENDS WITH '.tbi' THEN 'tbi'
  WHEN name ENDS WITH '.tif' THEN 'tif'
  WHEN name ENDS WITH '.xls' THEN 'xls'
  WHEN name ENDS WITH '.xlsx' THEN 'xlsx'
  ELSE 'Unknown'
END""".strip()

_SIZE = """
CASE
  WHEN sz >= 1024 * 1024 * 1024 THEN
    CASE
      WHEN round(toFloat(sz) / (1024.0 * 1024.0 * 1024.0), 2) = toInteger(round(toFloat(sz) / (1024.0 * 1024.0 * 1024.0)))
        THEN toString(toInteger(round(toFloat(sz) / (1024.0 * 1024.0 * 1024.0)))) + ' GB'
      ELSE toString(round(toFloat(sz) / (1024.0 * 1024.0 * 1024.0), 2)) + ' GB'
    END
  WHEN sz >= 1024 * 1024 THEN
    CASE
      WHEN round(toFloat(sz) / (1024.0 * 1024.0), 2) = toInteger(round(toFloat(sz) / (1024.0 * 1024.0)))
        THEN toString(toInteger(round(toFloat(sz) / (1024.0 * 1024.0)))) + ' MB'
      ELSE toString(round(toFloat(sz) / (1024.0 * 1024.0), 2)) + ' MB'
    END
  WHEN sz >= 1024 THEN
    CASE
      WHEN round(toFloat(sz) / 1024.0, 2) = toInteger(round(toFloat(sz) / 1024.0))
        THEN toString(toInteger(round(toFloat(sz) / 1024.0))) + ' KB'
      ELSE toString(round(toFloat(sz) / 1024.0, 2)) + ' KB'
    END
  ELSE
    CASE
      WHEN round(toFloat(sz), 2) = toInteger(round(toFloat(sz)))
        THEN toString(toInteger(round(toFloat(sz)))) + ' Bytes'
      ELSE toString(round(toFloat(sz), 2)) + ' Bytes'
    END
END""".strip()


def stat_query(f: IcdcFilters) -> str:
    return f"""
{_core_case_filter(f)}
WITH DISTINCT c, s, p
OPTIONAL MATCH (samp:sample)-[:of_case]->(c)
OPTIONAL MATCH (f:file)-[*]->(samp)
OPTIONAL MATCH (sf:file)-->(s)
RETURN count(DISTINCT p.program_acronym) AS Programs,
       count(DISTINCT s.clinical_study_designation) AS Studies,
       count(DISTINCT c.case_id) AS Cases,
       count(DISTINCT samp) AS Samples,
       count(DISTINCT f) AS `Case Files`,
       count(DISTINCT sf) AS `Study Files`
""".strip()


def cases_tab_query(f: IcdcFilters) -> str:
    return f"""
{_core_case_filter(f)}
OPTIONAL MATCH (c)-[:member_of]->(co:cohort)
WITH DISTINCT c, s, demo, diag, co
RETURN c.case_id AS `Case ID`,
       s.clinical_study_designation AS `Study Code`,
       s.clinical_study_type AS `Study Type`,
       demo.breed AS Breed,
       diag.disease_term AS Diagnosis,
       diag.stage_of_disease AS `Stage Of Disease`,
       {_AGE} AS Age,
       coalesce(trim(toString(demo.sex)), '') AS Sex,
       coalesce(toString(demo.neutered_indicator), '') AS `Neutered Status`,
       coalesce({_WEIGHT}, '') AS `Weight (kg)`,
       coalesce(diag.best_response, '') AS `Response to Treatment`,
       coalesce(co.cohort_description, '') AS Cohort
ORDER BY c.case_id ASC
LIMIT 100
""".strip()


def samples_tab_query(f: IcdcFilters) -> str:
    return f"""
{_core_case_filter(f)}
MATCH (samp:sample)-[:of_case]->(c)
RETURN DISTINCT samp.sample_id AS `Sample ID`,
       c.case_id AS `Case ID`,
       coalesce(demo.breed, '') AS Breed,
       coalesce(diag.disease_term, '') AS Diagnosis,
       coalesce(samp.sample_site, '') AS `Sample Site`,
       coalesce(samp.summarized_sample_type, '') AS `Sample Type`,
       coalesce(samp.specific_sample_pathology, '') AS `Pathology/Morphology`,
       coalesce(samp.tumor_grade, '') AS `Tumor Grade`,
       coalesce(samp.sample_chronology, '') AS `Sample Chronology`,
       coalesce(samp.percentage_tumor, '') AS `Percentage Tumor`,
       coalesce(samp.necropsy_sample, '') AS `Necropsy Sample`,
       coalesce(samp.sample_preservation, '') AS `Sample Preservation`
ORDER BY samp.sample_id ASC
LIMIT 100
""".strip()


def case_files_tab_query(f: IcdcFilters) -> str:
    fmt = _FORMAT_FROM_NAME.replace("name", "f.file_name")
    size = _SIZE.replace("sz", "f.file_size")
    return f"""
{_core_case_filter(f)}
MATCH (samp:sample)-[:of_case]->(c)
MATCH (f:file)-[*]->(samp)
RETURN DISTINCT f.file_name AS `File Name`,
       {fmt} AS Format,
       f.file_type AS `File Type`,
       {size} AS Size,
       'sample' AS Association,
       f.file_description AS Description,
       samp.sample_id AS `Sample ID`,
       c.case_id AS `Case ID`,
       demo.breed AS Breed,
       diag.disease_term AS Diagnosis
ORDER BY f.file_name ASC
LIMIT 100
""".strip()


def study_files_tab_query(f: IcdcFilters) -> str:
    fmt = _FORMAT_STUDY.replace("name", "sf.file_name")
    size = _SIZE.replace("sz", "sf.file_size")
    return f"""
{_core_case_filter(f)}
WITH DISTINCT s
MATCH (sf:file)-->(s)
RETURN DISTINCT sf.file_name AS `File Name`,
       sf.file_type AS `File Type`,
       'study' AS Association,
       sf.file_description AS Description,
       {fmt} AS Format,
       {size} AS Size,
       s.clinical_study_designation AS `Study Code`
ORDER BY sf.file_name ASC
LIMIT 100
""".strip()


def from_cypher_filters(cypher: str) -> IcdcFilters:
    """Rebuild IcdcFilters from an existing CasesTab/StatQuery WHERE clause."""
    study = ""
    m = re.search(r"clinical_study_designation:\s*'([^']+)'", cypher)
    if m:
        study = m.group(1)
    if not study:
        m = re.search(r"clinical_study_designation\s*=\s*'([^']+)'", cypher)
        if m:
            study = m.group(1)
    preds: List[Tuple[str, str, str, str]] = []
    for var, prop, mode in (
        ("s", "clinical_study_type", "eq"),
        ("demo", "breed", "eq"),
        ("diag", "disease_term", "eq"),
        ("diag", "primary_disease_site", "eq"),
        ("diag", "stage_of_disease", "eq"),
        ("diag", "best_response", "eq"),
    ):
        m = re.search(rf"{var}\.{prop}\s*=\s*'([^']+)'", cypher)
        if m:
            preds.append((var, prop, m.group(1), mode))
    if "registration_origin" in cypher and "Not Applicable" in cypher:
        preds.append(("__biobank__", "registration_origin", "Not Applicable", "eq"))
    else:
        m = re.search(r"registration_origin\s*=\s*'([^']+)'", cypher)
        if m:
            preds.append(("__biobank__", "registration_origin", m.group(1), "eq"))
    return IcdcFilters(study_code=study, predicates=preds)


def filters_from_cases_tab(text: str) -> IcdcFilters:
    if text.lstrip().upper().startswith("MATCH"):
        f = from_cypher_filters(text)
    else:
        f = IcdcFilters.from_cases_sql(text)
    if not f.study_code:
        raise ValueError("Could not parse study code from CasesTab query")
    return f


def all_queries_from_cases_sql(cases_sql: str) -> dict[str, str]:
    f = filters_from_cases_tab(cases_sql)
    return {
        "StatQuery": stat_query(f),
        "CasesTab": cases_tab_query(f),
        "SamplesTab": samples_tab_query(f),
        "CaseFilesTab": case_files_tab_query(f),
        "StudyFilesTab": study_files_tab_query(f),
    }
