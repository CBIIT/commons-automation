"""
INS (Index of NCI Studies): https://studycatalog.cancer.gov

Programs or Datasets explore: stat bar + result tabs (Programs, Projects, Grants, Publications).
Expected data: TSV from Programs.zip / DataSetsTab.zip (extracted under InputFiles/INS/) + SQL in TC*.xlsx.
"""
from Commons import action_log, excel_writer
from Commons.base_app import BaseApp, StatSpec, TabSpec
from Commons.compare import compare_tables
from Commons.apps.ins.tsv_source import InsTsvSource, read_ins_datasets_page_table

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

    def verify_datasets(self):
        """Katalon verifyUiAgainstTsvForInsDatasetsTab: card grid vs DatasetsTab SQL + DataSetsTab TSV."""
        if self.query_file is None:
            raise RuntimeError("Call load_query_file() first")
        action_log.ui_action("Reading INS Datasets cards from UI.")
        ui_table = read_ins_datasets_page_table(self.ui, self.repo)
        source = self.connected_source()
        if not isinstance(source, InsTsvSource):
            raise RuntimeError("INS Datasets compare requires expected_source: tsv")
        expected = source.fetch_ins_datasets_table(self.query_file)
        ui_table.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])
        expected.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])
        base = self.output_dir / self.query_file.name
        excel_writer.write_sheet(
            base.with_name(base.name + "_UI.xlsx"), "UI_Datasets", ui_table.header, ui_table.rows
        )
        excel_writer.write_sheet(
            base.with_name(base.name + "_DB.xlsx"), "DB_Datasets", expected.header, expected.rows
        )
        action_log.compare_step("UI_Datasets", "DB_Datasets")
        cmp = compare_tables(ui_table.rows, expected.rows, ui_table.header, expected.header)
        self._record("Datasets", cmp, ui_count=len(ui_table.rows), exp_count=len(expected.rows))
