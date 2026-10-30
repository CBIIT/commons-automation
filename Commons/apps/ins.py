"""INS (Index of NCI Studies): https://studycatalog.cancer.gov"""
from Commons import action_log
from Commons.apps.base import BaseApp, StatSpec, TabSpec


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


class INS(BaseApp):
    NAME = "INS"
    BANNER_KEYS = ["Navbar/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "INS_StaticData.xlsx"

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

    def open_programs(self):
        """Programs explore (Katalon: INS/Navbar/Programs-Btn)."""
        self.click("Navbar/Programs-Btn", ui_message="INS Programs page opened successfully.")

    def open_datasets(self):
        """Datasets explore (Katalon: INS/Navbar/Datasets-Btn)."""
        self.click("Navbar/Datasets-Btn", ui_message="INS Datasets page opened successfully.")

    def verify_datasets_tab(self):
        """DataSets explore: card grid + DatasetsTab SQL (not Programs result tabs)."""
        from Commons.compare import compare_tables
        from Commons import excel_writer
        from Commons.ins_datasets_reader import read_ins_datasets_ui
        from Commons.tab_setting import tab_is_enabled

        if self.query_file is None:
            raise RuntimeError("Call load_query_file() first")
        if not tab_is_enabled(self.settings.tab_execution, "Datasets"):
            action_log.ui_action("Skipped Datasets tab (disabled in Config/tab_setting.yaml).")
            self.results.append(
                {"check": "Datasets", "status": "SKIPPED", "detail": "disabled in tab_setting.yaml"}
            )
            return
        self.ui.wait_idle()
        ui_table = read_ins_datasets_ui(
            self.ui,
            self.repo,
            max_pages=self.settings.pagination_max_pages or 50,
        )
        expected = self.source.fetch_tab_table(
            self.query_file,
            "DatasetsTab",
            tab_display_name="Datasets",
        )
        ui_table.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])
        expected.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])
        if self.settings.tab_row_limit and self.settings.tab_row_limit > 0:
            ui_table.rows = ui_table.rows[: self.settings.tab_row_limit]
        base = self.output_dir / self.query_file.name
        excel_writer.write_sheet(
            base.with_name(base.name + "_UI.xlsx"), "WebDatasets", ui_table.header, ui_table.rows
        )
        excel_writer.write_sheet(
            base.with_name(base.name + "_DB.xlsx"), "TsvDatasets", expected.header, expected.rows
        )
        action_log.compare_step("WebDatasets", "TsvDatasets")
        cmp = compare_tables(ui_table.rows, expected.rows, ui_table.header, expected.header)
        self._record("Datasets", cmp, ui_count=len(ui_table.rows), exp_count=len(expected.rows))
