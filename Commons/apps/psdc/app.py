"""Population Science Data Commons: study exploration with TSV + SQL comparisons."""
from urllib.parse import quote

from Commons.result_tabs import ResultTabsApp
from Commons.apps.psdc.result_tabs import PSDCResultTabs
from Commons.base_app import BaseApp, StatSpec, TabSpec
from Commons.apps.psdc.homepage import HomePageControls


class PSDC(ResultTabsApp, HomePageControls, BaseApp):
    RESULT_TABS_CLASS = PSDCResultTabs
    NAME = "PSDC"
    BANNER_KEYS = ["Home/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "PSDC_StaticData.xlsx"

    STATS = [
        StatSpec("Studies", "Statbar/Studies-Count"),
        StatSpec("Participants", "Statbar/Participants-Count"),
        StatSpec("Cancer Types", "Statbar/CancerTypes-Count"),
        StatSpec("Data Categories", "Statbar/DataCategories-Count"),
        StatSpec("Study Files", "Statbar/StudyFiles-Count"),
    ]

    # PSDC Explore presents study summaries; participants are not a results tab.
    TABS = {
        "Studies": TabSpec(
            name="Studies",
            tab="ResultTabs/Studies-Tab",
            table="ResultTabs/Studies-Tbl",
            header="ResultTabs/Studies-TblHdr",
            next="ResultTabs/All_Tabs_Next-Btn",
            input_tab="StudiesTab",
            stat="Studies",
            ui_sheet="UI_Studies",
            db_sheet="DB_Studies",
            max_pages=25,
            label="Studies",
        ),
    }
    STANDARD_VERIFY_TABS = ("Studies",)

    def open_tab(self, name: str):
        # Explore has a single Studies table and no selectable tab on some releases.
        if name == 'Studies':
            self.ui.wait_visible(self.repo.xpath(self.TABS[name].table))
            return
        return super().open_tab(name)

    def open_explore(self):
        """Open the study search page using the navigation link."""
        self.click("NavBar/Explore-Btn", ui_message="PSDC Explore opened successfully.")

    def select_study(self, study: str):
        """Filter Explore by a study acronym, such as NLST, PBCS, or PLCO."""
        self.select_filter("Studies/Study", study)

    def open_study(self, study: str):
        """Open a study's detail page for its overview, summaries, and study files."""
        self.goto(f"#/study/{quote(study, safe='')}")
        self.ui.wait_visible(self.repo.xpath("StudyDetails/Overview-Tab"))

    # -----------------------------------------------------------------------
    # Result-table sorting: reuse discovery, both directions, and row retention
    # -----------------------------------------------------------------------

    def result_tab_sorting_options(self, tab):
        from Commons.apps.psdc.table_sorting import sorting_options
        return sorting_options(self, tab)
