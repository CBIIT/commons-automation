"""CTDC (Clinical Trials Data Commons): https://clinical-qa.datacommons.cancer.gov"""
from Commons.apps.base import BaseApp, StatSpec, TabSpec  # TabSpec used for Study Files tab


def _tab(name, input_tab, stat, ui, db, max_pages=10):
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


class CTDC(BaseApp):
    NAME = "CTDC"
    BANNER_KEYS = ["Home/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "TC01_CTDC_StaticData.xlsx"

    STATS = [
        StatSpec("Studies", "Statbar/Studies-Count"),
        StatSpec("Participants", "Statbar/Participants-Count"),
        StatSpec("Diagnoses", "Statbar/Diagnoses-Count"),
        StatSpec("Targeted Therapies", "Statbar/TargetedTherapies-Count"),
        StatSpec("Biospecimens", "Statbar/Biospecimens-Count"),
        StatSpec("Files", "Statbar/Files-Count"),
    ]

    TABS = {
        "Participants": _tab(
            "Participants", "ParticipantsTab", "Participants", "UI_Participants", "DB_Participants"
        ),
        "Biospecimens": _tab(
            "Biospecimens", "BiospecimensTab", "Biospecimens", "UI_Biospecimens", "DB_Biospecimens"
        ),
        "Files": _tab("Files", "FilesTab", "Files", "UI_Files", "DB_Files"),
        "Study Files": TabSpec(
            name="Study Files",
            tab="ResultTabs/StudyFiles-Tab",
            table="ResultTabs/StudyFiles-Tbl",
            header="ResultTabs/StudyFiles-TblHdr",
            next="ResultTabs/All_Tabs_Next-Btn",
            input_tab="StudyFilesTab",
            stat="Participants",
            ui_sheet="UI_StudyFiles",
            db_sheet="DB_StudyFiles",
            max_pages=10,
            label="Study Files",
        ),
    }

    STANDARD_VERIFY_TABS: tuple = (
        "Participants",
        "Biospecimens",
        "Files",
        "Study Files",
    )

    def open_explore(self):
        """Open Explore via navbar (Katalon: clickTab CTDC/NavBar/Explore-Btn)."""
        self.click("NavBar/Explore-Btn", ui_message="Explore opened successfully.")
