"""
CCDI Hub: https://ccdi.cancer.gov

Hub-only tests (home, about, policies). Navbar Explore opens C3DC Explore Participants —
there is no CCDI-specific Explore or result tabs.
"""
from Commons.apps.base import BaseApp, StatSpec

# ---------------------------------------------------------------------------
# App adapter (static pages + handoff to C3DC Explore)
# ---------------------------------------------------------------------------


class CCDI(BaseApp):
    NAME = "CCDI"
    BANNER_KEYS = ["Navbar/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "TC01_CCDI_StaticData.xlsx"
    TABS = {}  # Hub has no Explore result tabs

    # --- Stat bar (where static / cross-portal tests read counts) ---

    STATS = [
        StatSpec("Studies", "Statbar/Studies_Cnt"),
        StatSpec("Participants", "Statbar/Participants_Cnt"),
        StatSpec("Samples", "Statbar/Samples_Cnt"),
        StatSpec("Files", "Statbar/Files_Cnt"),
    ]

    # --- Navigation ---

    def open_explore(self):
        """Explore menu → C3DC Explore Participants (not a CCDI explore URL)."""
        self.click(
            "Navbar/Explore_Menu",
            ui_message="C3DC Explore Participants opened from CCDI Explore.",
        )
