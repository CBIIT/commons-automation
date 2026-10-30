"""
ICDC (Integrated Canine Data Commons): https://caninecommons-qa.cancer.gov

Cases explore: stat bar + result tabs (Cases, Samples, Case Files, Study Files).
Expected data: Neo4j Cypher in InputFiles/ICDC/TC*.xlsx.
"""
from Commons.apps.base import BaseApp, StatSpec, TabSpec

# ---------------------------------------------------------------------------
# Tab wiring (workbook TabQuery keys ↔ Canine result tab locators)
# ---------------------------------------------------------------------------


def _tab(name, input_tab, stat, ui_sheet, db_sheet, tab_key, table, header, next_key, max_pages=10):
    return TabSpec(
        name=name,
        tab=tab_key,
        table=table,
        header=header,
        next=next_key,
        input_tab=input_tab,
        stat=stat,
        ui_sheet=ui_sheet,
        db_sheet=db_sheet,
        max_pages=max_pages,
        label=name,
    )


# ---------------------------------------------------------------------------
# App adapter
# ---------------------------------------------------------------------------


class ICDC(BaseApp):
    NAME = "ICDC"
    BANNER_KEYS = ["Canine_PopUp_Continue_Btn"]

    # --- Stat bar and result tabs ---

    STATS = [
        StatSpec("Programs", "StatBar/Canine_StatBar-Programs"),
        StatSpec("Studies", "StatBar/Canine_StatBar-Studies"),
        StatSpec("Cases", "StatBar/Canine_StatBar-Cases"),
        StatSpec("Samples", "StatBar/Canine_StatBar-Samples"),
        StatSpec("Case Files", "StatBar/Canine_StatBar-CaseFiles"),
        StatSpec("Study Files", "StatBar/Canine_StatBar-StudyFiles"),
    ]

    TABS = {
        "Cases": _tab(
            "Cases",
            "CasesTab",
            "Cases",
            "UI_Cases",
            "DB_Cases",
            "CanineResults_Cases_Tab",
            "Canine_CasesTable",
            "Canine_TableHeader",
            "Canine_CasesTabNextBtn",
        ),
        "Samples": _tab(
            "Samples",
            "SamplesTab",
            "Samples",
            "UI_Samples",
            "DB_Samples",
            "CanineResults_Samples_Tab",
            "Canine_Samples_Table",
            "Canine_Samples_TableHdr",
            "Canine_SamplesTabNextBtn",
        ),
        "Case Files": _tab(
            "Case Files",
            "CaseFilesTab",
            "Case Files",
            "UI_CaseFiles",
            "DB_CaseFiles",
            "CanineResults_CaseFiles_Tab",
            "Canine_Files_Table",
            "Canine_Files_TableHdr",
            "Canine_FilesTabNextBtn",
        ),
        "Study Files": _tab(
            "Study Files",
            "StudyFilesTab",
            "Study Files",
            "UI_StudyFiles",
            "DB_StudyFiles",
            "CanineResults_StudyFiles_Tab",
            "Canine_StudyFiles_Table",
            "Canine_StudyFiles_TableHdr",
            "Canine_StudyFilesTabNextBtn",
        ),
    }

    STANDARD_VERIFY_TABS = ("Cases", "Samples", "Case Files", "Study Files")

    # --- Explore navigation ---

    def open_cases(self):
        """Open Cases explore via navbar (Katalon: NavBar Canine_Cases_Btn)."""
        self.click("NavBar/Canine_Cases_Btn", ui_message="Cases (Explore) opened successfully.")

    def select_study(self, study_checkbox: str = "Canine_Filter_Study-COTC021"):
        """Tick the study checkbox before other filters (default COTC021)."""
        self.select_filter("Cases/Study", study_checkbox)
