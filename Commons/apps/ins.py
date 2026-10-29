"""
INS (Index of NCI Studies): https://studycatalog.cancer.gov

Programs or Datasets explore: stat bar + result tabs (Programs, Projects, Grants, Publications).
Expected data: TSV from Program.zip / DataSetsTab.zip (extracted under InputFiles/INS/) + SQL in TC*.xlsx.
"""
from Commons.apps.base import BaseApp, StatSpec, TabSpec

# ---------------------------------------------------------------------------
# Tab wiring (workbook TabQuery keys ↔ ResultTabs locators)
# ---------------------------------------------------------------------------


def _tab(name: str, input_tab: str, stat: str, ui: str, db: str, max_pages: int = 10) -> TabSpec:
    return TabSpec(
        name=name,
        tab=f"ResultTabs/{name}-Tab",
        table=f"ResultTabs/{name}-Tbl",
        header=f"ResultTabs/{name}-TblHdr",
        next="ResultTabs/All_Tabs_Next-Btn",
        input_tab=input_tab,
        stat=stat,
        ui_sheet=ui,
        db_sheet=db,
        max_pages=max_pages,
        label=name,
    )


# ---------------------------------------------------------------------------
# App adapter
# ---------------------------------------------------------------------------


class INS(BaseApp):
    NAME = "INS"
    BANNER_KEYS = ["Navbar/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "INS_StaticData.xlsx"

    # --- Stat bar and result tabs ---

    STATS = [
        StatSpec("Programs", "Statbar/Statbar-Programs"),
        StatSpec("Projects", "Statbar/Statbar-Projects"),
        StatSpec("Grants", "Statbar/Statbar-Grants"),
        StatSpec("Publications", "Statbar/Statbar-Publications"),
    ]

    TABS = {
        "Programs": _tab("Programs", "ProgramsTab", "Programs", "UI_Programs", "DB_Programs"),
        "Projects": _tab("Projects", "ProjectsTab", "Projects", "UI_Projects", "DB_Projects"),
        "Grants": _tab("Grants", "GrantsTab", "Grants", "UI_Grants", "DB_Grants"),
        "Publications": _tab(
            "Publications", "PublicationsTab", "Publications", "UI_Publications", "DB_Publications"
        ),
    }

    STANDARD_VERIFY_TABS: tuple = (
        "Programs",
        "Projects",
        "Grants",
        "Publications",
    )

    # --- Explore navigation ---

    def open_programs(self):
        """Open Programs explore via navbar (Katalon: INS/Navbar/Programs-Btn)."""
        self.click("Navbar/Programs-Btn", ui_message="INS Programs page opened successfully.")

    def open_datasets(self):
        """Open Datasets explore via navbar (Katalon: INS/Navbar/Datasets-Btn)."""
        self.click("Navbar/Datasets-Btn", ui_message="INS Datasets page opened successfully.")
