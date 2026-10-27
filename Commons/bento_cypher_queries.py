"""Neo4j Cypher for Bento arm-* expected data (TAILORx graph model)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from Commons.bento_arm_filters import ArmLetter, ArmFacetChoice, BentoFacetSpec

# UI / SQL workbook column aliases (must match Bento results tables).
_CASES_RETURN = """
RETURN DISTINCT
  ss.study_subject_id AS `Case ID`,
  p.program_acronym AS `Program Code`,
  p.program_id AS `Program ID`,
  s.study_acronym AS `ARM`,
  ss.disease_subtype AS `Diagnosis`,
  sf.grouped_recurrence_score AS `Recurrence Score`,
  d.tumor_size_group AS `Tumor Size (cm)`,
  d.er_status AS `ER Status`,
  d.pr_status AS `PR Status`,
  coalesce(
    CASE demo.age_at_index % 1
      WHEN 0 THEN toInteger(demo.age_at_index)
      ELSE demo.age_at_index
    END,
    ''
  ) AS `Age (years)`,
  CASE WHEN demo.survival_time = 0 THEN '' ELSE demo.survival_time END AS `Survival (days)`
ORDER BY ss.study_subject_id ASC
LIMIT 100
""".strip()

_SAMPLES_RETURN = """
RETURN DISTINCT
  samp.sample_id AS `Sample ID`,
  ss.study_subject_id AS `Case ID`,
  p.program_acronym AS `Program Code`,
  s.study_acronym AS `ARM`,
  ss.disease_subtype AS `Diagnosis`,
  samp.tissue_type AS `Tissue Type`,
  samp.composition AS `Tissue Composition`,
  samp.sample_anatomic_site AS `Sample Anatomic Site`,
  samp.method_of_sample_procurement AS `Sample Procurement Method`,
  lp.test_name AS platform
ORDER BY samp.sample_id ASC
LIMIT 100
""".strip()

_FILE_SIZE_EXPR = """
CASE
  WHEN f.file_size >= 1073741824 THEN toString(round(f.file_size / 1073741824.0, 2)) + ' GB'
  WHEN f.file_size >= 1048576 THEN toString(round(f.file_size / 1048576.0, 2)) + ' MB'
  WHEN f.file_size >= 1024 THEN toString(round(f.file_size / 1024.0, 2)) + ' KB'
  ELSE toString(toInteger(f.file_size)) + ' Bytes'
END
""".strip()

_FILES_RETURN = f"""
RETURN DISTINCT
  f.file_name AS `File Name`,
  head(labels(parent)) AS `Association`,
  f.file_description AS `Description`,
  f.file_format AS `File Format`,
  {_FILE_SIZE_EXPR} AS `Size`,
  p.program_acronym AS `Program Code`,
  s.study_acronym AS `ARM`,
  ss.study_subject_id AS `Case ID`,
  samp.sample_id AS `Sample ID`
ORDER BY f.file_name ASC
LIMIT 100
""".strip()

_SUBJECT_CONTEXT = """
MATCH (ss)<-[:sf_of_study_subject]-(sf:stratification_factor)
MATCH (ss)<-[:diagnosis_of_study_subject]-(d:diagnosis)<-[:tp_of_diagnosis]-(tp:therapeutic_procedure)
MATCH (ss)<-[:demographic_of_study_subject]-(demo:demographic_data)
""".strip()


def _filtered_subject_prefix(
    arm: ArmLetter,
    extra_match: str,
    anchor_preds: list[str],
    context_preds: list[str],
) -> str:
    """Arm filter first, then facet vars only after sf/d/tp/demo are matched."""
    parts = [
        "MATCH (ss:study_subject)-[:study_subject_of_study]->(s:study)-[:study_of_program]->(p:program)",
    ]
    if extra_match.strip():
        parts.append(extra_match.strip())
    where = [_arm_where(arm), *anchor_preds]
    parts.append("WHERE " + " AND ".join(where))
    parts.append("WITH ss, s, p")
    parts.append(_SUBJECT_CONTEXT)
    if context_preds:
        parts.append("WHERE " + " AND ".join(context_preds))
    return "\n".join(parts)

_DIAGNOSIS_VALUE: Dict[str, str] = {
    "Adenocarcinoma": "Adenocarcinoma",
    "Comedocarcinoma": "Comedocarcinoma",
    "NotReported": "Not Reported",
    "TubularCarcinoma": "Tubular Carcinoma",
}

_RECURRENCE_SCORE: Dict[str, str] = {
    "00_to_05": "0-5",
    "06_to_10": "6-10",
    "11_to_15": "11-15",
    "16_to_20": "16-20",
    "21_to_25": "21-25",
    "26_to_30": "26-30",
    "31_to_35": "31-35",
    "36_to_40": "36-40",
    "41_to_50": "41-50",
    "51_to_100": "51-100",
}

_TUMOR_SIZE: Dict[str, str] = {
    "1_to_2": "(1,2]",
    "2_to_3": "(2,3]",
    "3_to_4": "(3,4]",
    "Above_4": ">4",
    "Below_1": "<=1",
    "NotReported": "Not Reported",
}

_TUMOR_GRADE: Dict[str, str] = {
    "High": "High Grade",
    "Intermediate": "Intermediate Grade",
    "Low": "Low Grade",
    "NotReported": "Not Reported",
}

_CHEMO_REGIMEN: Dict[str, str] = {
    "DoseDenseAC2WkCycle": "Dose dense AC (2 week cycles)",
    "DoseDenseACTaxane": "Dose dense AC followed by a taxane",
    "IVCMF-3WkCycle": "IV CMF (3 week cycles)",
    "None": "None",
    "TaxaneOnly": "Taxane only",
    "TC-3WkCycle": "TC (3 week cycles, includes any taxane with cyclophosphamide)",
}

_FILE_TYPE: Dict[str, str] = {
    "Text": "text",
    "Bai": "bai",
    "Vcf": "vcf",
    "Bam": "bam",
}


@dataclass
class BentoQueryBundle:
    cases_tab: str
    samples_tab: str
    files_tab: str
    stat_query: str


def is_sql_query(text: str) -> bool:
    return bool(text and text.strip().upper().startswith("SELECT"))


def is_cypher_query(text: str) -> bool:
    t = text.strip().upper()
    return bool(text and ("MATCH" in t or t.startswith("WITH")))


def patch_arm_filter(cypher: str, arm: ArmLetter) -> str:
    """Ensure every query filters TAILORx arm (study acronym A–D)."""
    clause = f"s.study_acronym = '{arm}'"
    if re.search(r"study_acronym\s*=\s*'[ABCD]'", cypher):
        return re.sub(r"study_acronym\s*=\s*'[ABCD]'", clause, cypher)
    if re.search(r"\bWHERE\b", cypher, re.I):
        return re.sub(
            r"(\bWHERE\b\s+)(.*?)(\s+(?:WITH|MATCH|RETURN|return)\b)",
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} AND {clause}{m.group(3)}",
            cypher,
            count=1,
            flags=re.I | re.S,
        )
    return re.sub(
        r"\b(return|RETURN)\b",
        f"WHERE {clause}\nRETURN",
        cypher,
        count=1,
    )


def normalize_bento_cypher_aliases(cypher: str) -> str:
    """Align legacy Katalon Cypher column names with current UI/SQL workbooks."""
    text = cypher
    text = re.sub(r"\bas\s+`Arm`", "AS `ARM`", text, flags=re.I)
    text = re.sub(r"\bas\s+Program_ID\b", "AS `Program ID`", text, flags=re.I)
    text = re.sub(r"\bas\s+`tumor_size`", "AS `Tumor Size (cm)`", text, flags=re.I)
    text = text.replace("apoc.convert.toInteger", "toInteger")
    text = re.sub(
        r"demo\.survival_time\s+AS\s+`Survival \(days\)`",
        "CASE WHEN demo.survival_time = 0 THEN '' ELSE demo.survival_time END AS `Survival (days)`",
        text,
        flags=re.I,
    )
    return text


def _arm_where(arm: ArmLetter) -> str:
    return f"s.study_acronym = '{arm}'"


def _facet_predicates(
    spec: BentoFacetSpec, choice: ArmFacetChoice
) -> tuple[str, list[str], list[str]]:
    """Return (extra_match, anchor_preds, context_preds) for facet filters."""
    fg = spec.filter_group
    fv = choice.filter_value
    extra = ""
    anchor: list[str] = []
    context: list[str] = []

    if choice.age_min is not None:
        hi = choice.age_max if choice.age_max is not None else choice.age_min
        context.append(f"demo.age_at_index >= {choice.age_min} AND demo.age_at_index <= {hi}")
    elif fg == "Filter/Diagnosis":
        anchor.append(f"ss.disease_subtype = {_quote(_DIAGNOSIS_VALUE.get(fv, fv))}")
    elif fg == "Filter/Recurrence Score":
        bucket = _RECURRENCE_SCORE[fv]
        context.append(f"sf.grouped_recurrence_score IN [{_quote(bucket)}]")
    elif fg == "Filter/TumorSize":
        context.append(f"d.tumor_size_group IN [{_quote(_TUMOR_SIZE[fv])}]")
    elif fg == "Filter/Chemotherapy":
        regimen = _CHEMO_REGIMEN[fv]
        if fv == "None":
            context.append("(tp.chemotherapy_regimen = 'None' OR tp.chemotherapy_regimen IS NULL)")
        else:
            context.append(f"tp.chemotherapy_regimen = {_quote(regimen)}")
    elif fg == "Filter/TumorGrade":
        context.append(f"d.tumor_grade IN [{_quote(_TUMOR_GRADE[fv])}]")
    elif fg == "Filter/ERStatus":
        context.append(f"d.er_status = {_quote(fv if fv != 'NotReported' else 'Not Reported')}")
    elif fg == "Filter/PRStatus":
        context.append(f"d.pr_status = {_quote(fv if fv != 'NotReported' else 'Not Reported')}")
    elif fg == "Filter/EndocrineTherapy":
        context.append(f"tp.endocrine_therapy_type = {_quote(fv)}")
    elif fg == "Filter/MenopauseStatus":
        label = "Postmenopausal" if fv == "Post" else "Premenopausal"
        context.append(f"demo.menopause_status = {_quote(label)}")
    elif fg == "Filter/TissueType":
        extra = "MATCH (ss)<-[:sample_of_study_subject]-(samp:sample)\n"
        anchor.append("samp.tissue_type IN ['Tumor']")
    elif fg == "Filter/TissueComposition":
        extra = "MATCH (ss)<-[:sample_of_study_subject]-(samp:sample)\n"
        anchor.append("samp.composition IN ['Solid Tissue']")
    elif fg == "Filter/FileAssociation":
        # UI File Association "sample" = files linked to a sample node (see Files tab `head(labels(parent))`).
        extra = ""
        anchor.append(
            "EXISTS { MATCH (ss)<-[:sample_of_study_subject]-(samp:sample)<-[:file_of_sample]-(fx:file) }"
        )
    elif fg == "Filter/FileType":
        pass  # applied when matching files in each tab query

    return extra, anchor, context


def _quote(value: str) -> str:
    return "'" + value.replace("'", "\\'") + "'"


def _cases_file_type_exists(file_type: str) -> str:
    return f"""
EXISTS {{
  MATCH (ss)<-[*..2]-(parent)<--(fx:file)
  WHERE fx.file_type = {_quote(file_type)}
}}
""".strip()


def build_sql_facet_queries(arm: ArmLetter, spec: BentoFacetSpec, choice: ArmFacetChoice) -> BentoQueryBundle:
    extra, anchor_preds, context_preds = _facet_predicates(spec, choice)
    prefix = _filtered_subject_prefix(arm, extra, anchor_preds, context_preds)

    cases_parts = [prefix]
    if spec.filter_group == "Filter/FileType":
        file_t = _FILE_TYPE[choice.filter_value]
        cases_parts.append(f"WHERE {_cases_file_type_exists(file_t)}")
    cases = "\n".join(cases_parts + [_CASES_RETURN])

    samples_parts = [
        prefix,
        "MATCH (ss)<-[:sample_of_study_subject]-(samp:sample)",
    ]
    if spec.filter_group == "Filter/FileType":
        file_t = _FILE_TYPE[choice.filter_value]
        samples_parts.append(
            f"WHERE EXISTS {{ MATCH (samp)<-[:file_of_sample]-(fx:file) WHERE fx.file_type = {_quote(file_t)} }}"
        )
    samples_parts.append(
        "OPTIONAL MATCH (samp)<-[:file_of_sample]-(f:file)-[:file_of_laboratory_procedure]->(lp:laboratory_procedure)"
    )
    samples = "\n".join(samples_parts + [_SAMPLES_RETURN])

    files_parts = [prefix, "MATCH (ss)<-[*..2]-(parent)<--(f:file)", "MATCH (f)-[*]->(samp:sample)"]
    file_filters: list[str] = []
    if spec.filter_group == "Filter/FileType":
        file_filters.append(f"f.file_type = {_quote(_FILE_TYPE[choice.filter_value])}")
    if spec.filter_group == "Filter/FileAssociation":
        file_filters.append("toLower(head(labels(parent))) = 'sample'")
    if file_filters:
        files_parts.append("WHERE " + " AND ".join(file_filters))
    files = "\n".join(files_parts + [_FILES_RETURN])

    stat = _build_stat_query(arm, spec, choice, extra, anchor_preds, context_preds)
    return BentoQueryBundle(cases, samples, files, stat)


def _build_stat_query(
    arm: ArmLetter,
    spec: BentoFacetSpec,
    choice: ArmFacetChoice,
    extra_match: str,
    anchor_preds: list[str],
    context_preds: list[str],
) -> str:
    parts = [_filtered_subject_prefix(arm, extra_match, anchor_preds, context_preds)]
    if spec.filter_group == "Filter/FileType":
        parts.extend(
            [
                "MATCH (ss)<-[*..2]-(parent)<--(f:file)",
                f"WHERE f.file_type = {_quote(_FILE_TYPE[choice.filter_value])}",
                "OPTIONAL MATCH (f)-[*]->(samp:sample)",
            ]
        )
        return "\n".join(
            parts
            + [
                "RETURN",
                "  count(DISTINCT p.program_id) AS Programs,",
                "  count(DISTINCT s.study_acronym) AS Arms,",
                "  count(DISTINCT ss.study_subject_id) AS Cases,",
                "  count(DISTINCT samp.sample_id) AS Samples,",
                "  count(DISTINCT f.file_id) AS Assays,",
                "  count(DISTINCT f.file_id) AS Files",
            ]
        )

    parts.extend(
        [
            "OPTIONAL MATCH (ss)<-[:sample_of_study_subject]-(samp:sample)",
            "OPTIONAL MATCH (samp)<-[:file_of_sample]-(f:file)",
            "OPTIONAL MATCH (f)-[:file_of_laboratory_procedure]->(lp:laboratory_procedure)",
        ]
    )
    if spec.filter_group == "Filter/FileAssociation":
        parts.append(
            "WHERE samp IS NOT NULL AND EXISTS { MATCH (samp)<-[:file_of_sample]-(fx:file) }"
        )

    return "\n".join(
        parts
        + [
            "RETURN",
            "  count(DISTINCT p.program_id) AS Programs,",
            "  count(DISTINCT s.study_acronym) AS Arms,",
            "  count(DISTINCT ss.study_subject_id) AS Cases,",
            "  count(DISTINCT samp.sample_id) AS Samples,",
            "  count(DISTINCT lp.laboratory_procedure_id) AS Assays,",
            "  count(DISTINCT f.file_id) AS Files",
        ]
    )


def finalize_cypher_from_katalon(cypher: str, arm: ArmLetter) -> str:
    text = normalize_bento_cypher_aliases(cypher.strip())
    text = patch_arm_filter(text, arm)
    return text


def build_queries_for_arm_test(
    arm: ArmLetter,
    spec: BentoFacetSpec,
    choice: ArmFacetChoice,
    katalon_workbooks_dir: Path | None = None,
) -> BentoQueryBundle:
    """Build Cases/Samples/Files/Stat Cypher for one arm facet workbook."""
    del katalon_workbooks_dir  # facet matrix drives queries; Katalon xlsx is reference only
    return build_sql_facet_queries(arm, spec, choice)
