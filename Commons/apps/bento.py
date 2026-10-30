"""
BENTO (TAILORx demo portal): https://bento-tools.org

Explore Cases view with stat bar (Programs … Files) and result tabs Cases / Samples / Files.
Expected data: Neo4j Cypher in InputFiles/BENTO/TC*.xlsx. Arm + facet matrix: Tools/bento_arm_filters.py.
"""
from Commons.apps.base import BaseApp, StatSpec, TabSpec

# ---------------------------------------------------------------------------
# Tab wiring (workbook TabQuery keys ↔ UI locators)
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


class Bento(BaseApp):
    NAME = "Bento"
    BANNER_KEYS = ["Banner/Bento_Warning_Continue_Btn"]
    STATIC_DATA_EXCEL = "Bento_StaticData.xlsx"

    STATS = [
        StatSpec("Programs", "StatBar/Bento_StatBar-Programs"),
        StatSpec("Arms", "StatBar/Bento_StatBar-Arms"),
        StatSpec("Cases", "StatBar/Bento_StatBar-Cases"),
        StatSpec("Samples", "StatBar/Bento_StatBar-Samples"),
        StatSpec("Assays", "StatBar/Bento_StatBar-Assays"),
        StatSpec("Files", "StatBar/Bento_StatBar-Files"),
    ]

    TABS = {
        "Cases": _tab(
            "Cases",
            "CasesTab",
            "Cases",
            "UI_Cases",
            "DB_Cases",
            "Cases_page/BentoResults_Cases_Tab",
            "Cases_page/Bento_CasesTable",
            "Cases_page/Bento_CasesTableHeader",
            "Cases_page/Bento_CasesTabNextBtn",
        ),
        "Samples": _tab(
            "Samples",
            "SamplesTab",
            "Samples",
            "UI_Samples",
            "DB_Samples",
            "Cases_page/BentoResults_Samples_Tab",
            "Cases_page/Bento_SamplesTable",
            "Cases_page/Bento_SamplesTableHeader",
            "Cases_page/Bento_SamplesTabNextBtn",
        ),
        "Files": _tab(
            "Files",
            "FilesTab",
            "Files",
            "UI_Files",
            "DB_Files",
            "Cases_page/BentoResults_Files_Tab",
            "Cases_page/Bento_FilesTable",
            "Cases_page/Bento_FilesTableHeader",
            "Cases_page/Bento_FilesTabNextBtn",
        ),
    }

    STANDARD_VERIFY_TABS = ("Cases", "Samples", "Files")

    # --- Navigation ---

    def open_cases(self):
        """NavBar Explore / Cases view (Katalon: Bento_Cases-Btn)."""
        self.click("NavBar/Bento_Cases-Btn", ui_message="Bento Explore (Cases) opened successfully.")

    # --- Sidebar filters (tests use select_filter explicitly; helpers optional) ---

    def select_arm(self, arm: str):
        """Arm facet A–D (TAILORx study arms)."""
        self.select_filter("Filter/Arm", arm)

    def open_filter_by_samples(self):
        self.click("Filters/Samples/FilterBySamples_Facet", ui_message="Filter By Samples section opened.")

    def open_filter_by_files(self):
        self.click("Filters/Files/FilterByFiles_Facet", ui_message="Filter By Files section opened.")

    def set_age_range(self, min_years: int, max_years: int):
        """Filter/Age min/max inputs (not a checkbox facet)."""
        g = self.repo.filter_group("Filter/Age")
        self._prepare_filter_panel(g, g.other["MinAge_Input"])
        self.ui.fill(g.other["MinAge_Input"], str(min_years), repo_key="Filter/Age/MinAge_Input")
        self.ui.fill(g.other["MaxAge_Input"], str(max_years), repo_key="Filter/Age/MaxAge_Input")
        self.ui.wait_idle()

    # --- Verify ---

    def verify_standard_tabs(self):
        for tab in self.STANDARD_VERIFY_TABS:
            self.verify_tab(tab)
