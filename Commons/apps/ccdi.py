"""CCDI Hub: https://ccdi.cancer.gov

CCDI has no Explore page of its own. Navbar Explore (/explore) opens
C3DC Explore Participants. This app covers Hub pages only (home, about, policies).
"""
from Commons.apps.base import BaseApp, StatSpec


class CCDI(BaseApp):
    NAME = "CCDI"
    BANNER_KEYS = ["Navbar/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "TC01_CCDI_StaticData.xlsx"
    TABS = {}

    STATS = [
        StatSpec("Studies", "Statbar/Studies_Cnt"),
        StatSpec("Participants", "Statbar/Participants_Cnt"),
        StatSpec("Samples", "Statbar/Samples_Cnt"),
        StatSpec("Files", "Statbar/Files_Cnt"),
    ]

    def open_explore(self):
        """Click Explore. Lands on C3DC Explore Participants, not a CCDI explore page."""
        self.click(
            "Navbar/Explore_Menu",
            ui_message="C3DC Explore Participants opened from CCDI Explore.",
        )
