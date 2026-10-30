"""Bento arm-* facet matrix (TC01–TC14 × arms A–D). Used by Tools/generate_bento_arm_tests.py and Tools/cypher/bento_cypher.py."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

ArmLetter = Literal["A", "B", "C", "D"]
ARMS: tuple[ArmLetter, ...] = ("A", "B", "C", "D")

ARM_SLUGS: dict[ArmLetter, str] = {
    "A": "arm-a",
    "B": "arm-b",
    "C": "arm-c",
    "D": "arm-d",
}

ARM_LABELS: dict[ArmLetter, str] = {
    "A": "A: RS 0-10, assigned endocrine therapy alone",
    "B": "B: RS 11-25, randomized to endocrine therapy alone",
    "C": "C: RS 11-25, randomized to chemo + endocrine therapy",
    "D": "D: RS > 25, assigned to chemo +",
}


@dataclass(frozen=True)
class ArmFacetChoice:
    """One arm's checkbox (+ Katalon workbook source for expected SQL)."""

    filter_value: str
    value_label: str
    slug: str
    katalon_workbook: str
    age_min: Optional[int] = None
    age_max: Optional[int] = None


@dataclass(frozen=True)
class BentoFacetSpec:
    tc: int
    filter_group: str
    facet_label: str
    by_arm: tuple[ArmFacetChoice, ArmFacetChoice, ArmFacetChoice, ArmFacetChoice]
    samples_section: bool = False
    files_section: bool = False


def choice_for_arm(spec: BentoFacetSpec, arm: ArmLetter) -> ArmFacetChoice:
    return spec.by_arm[ARMS.index(arm)]


def workbook_file_name(arm: ArmLetter, spec: BentoFacetSpec) -> str:
    slug = ARM_SLUGS[arm]
    choice = choice_for_arm(spec, arm)
    return f"TC{spec.tc:02d}_Bento_{slug}_{choice.slug}.xlsx"


def workbook_relative_path(arm: ArmLetter, spec: BentoFacetSpec) -> str:
    return workbook_file_name(arm, spec)


def _c(
    filter_value: str,
    value_label: str,
    slug: str,
    katalon: str,
    *,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
) -> ArmFacetChoice:
    return ArmFacetChoice(filter_value, value_label, slug, katalon, age_min, age_max)


# Order per facet: arm-a, arm-b, arm-c, arm-d (four distinct values where the UI provides them).
BENTO_FACET_SPECS: tuple[BentoFacetSpec, ...] = (
    BentoFacetSpec(
        1,
        "Filter/Diagnosis",
        "Diagnosis",
        (
            _c("Adenocarcinoma", "Adenocarcinoma", "Diagnosis-Adenocarcinoma", "TC01_Bento_Filter_Diagnosis-Adenocarcinoma.xlsx"),
            _c("Comedocarcinoma", "Comedocarcinoma", "Diagnosis-Comedocarcinoma", "TC03_Bento_Filter_Diagnosis-Comedocarcinoma.xlsx"),
            _c("NotReported", "Not Reported", "Diagnosis-NotReported", "TC09_Bento_Filter_Diagnosis-NotReported.xlsx"),
            _c("TubularCarcinoma", "Tubular Carcinoma", "Diagnosis-TubularCarcinoma", "TC12_Bento_Filter_Diagnosis-TubularCarcinoma.xlsx"),
        ),
    ),
    BentoFacetSpec(
        2,
        "Filter/Recurrence Score",
        "Recurrence Score",
        (
            _c("00_to_05", "0–5", "RecurrScore-00-05", "TC01_Bento_Filter_RecurrScore-00-05.xlsx"),
            _c("11_to_15", "11–15", "RecurrScore-11-15", "TC02_Bento_Filter_RecurrScore-11-15.xlsx"),
            _c("16_to_20", "16–20", "RecurrScore-16-20", "TC03_Bento_Filter_RecurrScore-16-20.xlsx"),
            _c("26_to_30", "26–30", "RecurrScore-26-30", "TC05_Bento_Filter_RecurrScore-26-30.xlsx"),
        ),
    ),
    BentoFacetSpec(
        3,
        "Filter/TumorSize",
        "Tumor Size",
        (
            _c("1_to_2", "(1,2]", "TumorSize-1-2", "TC01_Bento_Filter_TumorSize-1-2.xlsx"),
            _c("2_to_3", "(2,3]", "TumorSize-2-3", "TC02_Bento_Filter_TumorSize-2-3.xlsx"),
            _c("3_to_4", "(3,4]", "TumorSize-3-4", "TC03_Bento_Filter_TumorSize-3-4.xlsx"),
            _c("Above_4", ">4", "TumorSize-Above_4", "TC05_Bento_Filter_TumorSize-Above_4.xlsx"),
        ),
    ),
    BentoFacetSpec(
        4,
        "Filter/Chemotherapy",
        "Chemotherapy",
        (
            _c("None", "None", "Chemo-None", "TC05_Bento_Filter_Chemo-None.xlsx"),
            _c("IVCMF-3WkCycle", "IV CMF (3 week cycles)", "Chemo-IV_CMF", "TC04_Bento_Filter_Chemo-IV_CMF.xlsx"),
            _c("None", "None", "Chemo-None", "TC05_Bento_Filter_Chemo-None.xlsx"),
            _c(
                "DoseDenseACTaxane",
                "Dose dense AC followed by a taxane",
                "Chemo-DoseDenseAC2Taxane",
                "TC02_Bento_Filter_Chemo-DoseDenseAC2Taxane.xlsx",
            ),
        ),
    ),
    BentoFacetSpec(
        5,
        "Filter/TumorGrade",
        "Tumor Grade",
        (
            _c("High", "High Grade", "TumorGrade-HighGrade", "TC01_Bento_Filter_TumorGrade-HighGrade.xlsx"),
            _c("Intermediate", "Intermediate Grade", "TumorGrade-IntermediateGrade", "TC02_Bento_Filter_TumorGrade-IntermediateGrade.xlsx"),
            _c("Low", "Low Grade", "TumorGrade-LowGrade", "TC03_Bento_Filter_TumorGrade-LowGrade.xlsx"),
            _c("NotReported", "Not Reported", "TumorGrade-NotReported", "TC04_Bento_Filter_TumorGrade-NotReported.xlsx"),
        ),
    ),
    BentoFacetSpec(
        6,
        "Filter/ERStatus",
        "ER Status",
        (
            _c("Positive", "Positive", "ERStatus-Positive", "TC03_Bento_Filter_ERStatus-Positive.xlsx"),
            _c("Negative", "Negative", "ERStatus-Negative", "TC01_Bento_Filter_ERStatus-Negative.xlsx"),
            _c("Positive", "Positive", "ERStatus-Positive", "TC03_Bento_Filter_ERStatus-Positive.xlsx"),
            _c("NotReported", "Not Reported", "ERStatus-NotReported", "TC02_Bento_Filter_ERStatus-NotReported.xlsx"),
        ),
    ),
    BentoFacetSpec(
        7,
        "Filter/PRStatus",
        "PR Status",
        (
            _c("Positive", "Positive", "PRStatus-Positive", "TC03_Bento_Filter_PRStatus-Positive.xlsx"),
            _c("NotReported", "Not Reported", "PRStatus-NotReported", "TC02_Bento_Filter_PRStatus-NotReported.xlsx"),
            _c("Positive", "Positive", "PRStatus-Positive", "TC03_Bento_Filter_PRStatus-Positive.xlsx"),
            _c("NotReported", "Not Reported", "PRStatus-NotReported", "TC02_Bento_Filter_PRStatus-NotReported.xlsx"),
        ),
    ),
    BentoFacetSpec(
        8,
        "Filter/EndocrineTherapy",
        "Endocrine Therapy",
        (
            _c("AI", "AI", "EndocrineTherapy-AI", "TC01_Bento_Filter_EndocrineTherapy-AI.xlsx"),
            _c("None", "None", "EndocrineTherapy-None", "TC02_Bento_Filter_EndocrineTherapy-None.xlsx"),
            _c("OFS", "OFS", "EndocrineTherapy-OFS", "TC03_Bento_Filter_EndocrineTherapy-OFS.xlsx"),
            _c("Tam", "Tam", "EndocrineTherapy-Tam", "TC06_Bento_Filter_EndocrineTherapy-Tam.xlsx"),
        ),
    ),
    BentoFacetSpec(
        9,
        "Filter/MenopauseStatus",
        "Menopause Status",
        (
            _c("Post", "Postmenopausal", "MenoStatus-Post", "TC01_Bento_Filter_MenoStatus-Post.xlsx"),
            _c("Pre", "Premenopausal", "MenoStatus-Pre", "TC02_Bento_Filter_MenoStatus-Pre.xlsx"),
            _c("Post", "Postmenopausal", "MenoStatus-Post", "TC01_Bento_Filter_MenoStatus-Post.xlsx"),
            _c("Pre", "Premenopausal", "MenoStatus-Pre", "TC02_Bento_Filter_MenoStatus-Pre.xlsx"),
        ),
    ),
    BentoFacetSpec(
        10,
        "Filter/Age",
        "Age",
        (
            _c("", "10–30 years", "Age-10_to_30", "TC01_Bento_Filter_Age-10_to_30.xlsx", age_min=10, age_max=30),
            _c("", "31–45 years", "Age-31_to_45", "TC01_Bento_Filter_Age-10_to_30.xlsx", age_min=31, age_max=45),
            _c("", "46–60 years", "Age-46_to_60", "TC01_Bento_Filter_Age-10_to_30.xlsx", age_min=46, age_max=60),
            _c("", "61–75 years", "Age-61_to_75", "TC01_Bento_Filter_Age-10_to_30.xlsx", age_min=61, age_max=75),
        ),
    ),
    BentoFacetSpec(
        11,
        "Filter/TissueType",
        "Tissue Type",
        (
            _c("Tumor", "Tumor", "TissueType-Tumor", "TC01_Bento_Filter_TissueType-Tumor.xlsx"),
            _c("Tumor", "Tumor", "TissueType-Tumor", "TC01_Bento_Filter_TissueType-Tumor.xlsx"),
            _c("Tumor", "Tumor", "TissueType-Tumor", "TC01_Bento_Filter_TissueType-Tumor.xlsx"),
            _c("Tumor", "Tumor", "TissueType-Tumor", "TC01_Bento_Filter_TissueType-Tumor.xlsx"),
        ),
        samples_section=True,
    ),
    BentoFacetSpec(
        12,
        "Filter/TissueComposition",
        "Tissue Composition",
        (
            _c("SolidTissue", "Solid Tissue", "TissueComp-SolidTissue", "TC01_Bento_Filter_TissueComp-SolidTissue.xlsx"),
            _c("SolidTissue", "Solid Tissue", "TissueComp-SolidTissue", "TC01_Bento_Filter_TissueComp-SolidTissue.xlsx"),
            _c("SolidTissue", "Solid Tissue", "TissueComp-SolidTissue", "TC01_Bento_Filter_TissueComp-SolidTissue.xlsx"),
            _c("SolidTissue", "Solid Tissue", "TissueComp-SolidTissue", "TC01_Bento_Filter_TissueComp-SolidTissue.xlsx"),
        ),
        samples_section=True,
    ),
    BentoFacetSpec(
        13,
        "Filter/FileAssociation",
        "File Association",
        (
            _c("Sample", "sample", "FileAssoc-Sample", "TC01_Bento_Filter_FileAssoc-Sample.xlsx"),
            _c("Sample", "sample", "FileAssoc-Sample", "TC01_Bento_Filter_FileAssoc-Sample.xlsx"),
            _c("Sample", "sample", "FileAssoc-Sample", "TC01_Bento_Filter_FileAssoc-Sample.xlsx"),
            _c("Sample", "sample", "FileAssoc-Sample", "TC01_Bento_Filter_FileAssoc-Sample.xlsx"),
        ),
        files_section=True,
    ),
    BentoFacetSpec(
        14,
        "Filter/FileType",
        "File Type",
        (
            _c("Text", "text", "FileType-text", "TC01_Bento_Filter_FileType-text.xlsx"),
            _c("Bai", "bai", "FileType-bai", "TC02_Bento_Filter_FileType-bai.xlsx"),
            _c("Text", "text", "FileType-text", "TC01_Bento_Filter_FileType-text.xlsx"),
            _c("Text", "text", "FileType-text", "TC01_Bento_Filter_FileType-text.xlsx"),
        ),
        files_section=True,
    ),
)

# Back-compat alias for docs/tools
ARM_SECONDARY_FILTERS = BENTO_FACET_SPECS
