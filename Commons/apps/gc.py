"""GC (General Commons): https://datacommons.cancer.gov"""
from Commons.apps.base import BaseApp, StatSpec, TabSpec


def _tab(name, index_key, table, input_tab, stat, ui, db, max_pages=10):
    return TabSpec(
        name=name,
        tab=f"Data_page/{index_key}",
        table=f"Data_page/{table}Table",
        header=f"Data_page/{table}TableHeader",
        next=f"Data_page/{table}TabNextBtn",
        input_tab=input_tab, stat=stat, ui_sheet=ui, db_sheet=db,
        first_child=True, max_pages=max_pages,
    )


class GC(BaseApp):
    NAME = "GC"
    BANNER_KEYS = ["Popup_Continue_Btn"]
    STATIC_DATA_EXCEL = "GC_StaticData.xlsx"

    STATS = [
        StatSpec("Studies", "StatBar/GC_StatBar-Studies", use_html=True),
        StatSpec("Participants", "StatBar/GC_StatBar-Participants", use_html=True),
        StatSpec("Samples", "StatBar/GC_StatBar-Samples", use_html=True),
        StatSpec("Files", "StatBar/GC_StatBar-Files", use_html=True),
    ]

    TABS = {
        "Participants": _tab("Participants", "GCResults_Participants_Tab", "GC_Participants",
                             "ParticipantsTab", "Participants", "UI_Participants", "DB_Participants"),
        "Samples":      _tab("Samples", "GCResults_Samples_Tab", "GC_Samples",
                             "SamplesTab", "Samples", "UI_Samples", "DB_Samples"),
        "Files":        _tab("Files", "GCResults_Files_Tab", "GC_Files",
                             "FilesTab", "Files", "UI_Files", "DB_Files"),
    }

    def open_data(self):
        self.click("NavBar/GC_Data-Btn")
