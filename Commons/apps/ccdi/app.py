"""
CCDI Hub: https://ccdi.cancer.gov

Hub-only tests (home, about, policies). Navbar Explore opens C3DC Explore Participants —
there is no CCDI-specific Explore or result tabs.
"""
from playwright.sync_api import Error as PlaywrightError

from Commons.base_app import BaseApp, StatSpec

# ---------------------------------------------------------------------------
# App adapter (static pages + handoff to C3DC Explore)
# ---------------------------------------------------------------------------


class CCDI(BaseApp):
    NAME = "CCDI"
    BANNER_KEYS = ["Navbar/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "CCDI_StaticData.xlsx"
    TABS = {}  # Hub has no Explore result tabs

    # --- Stat bar (where static / cross-portal tests read counts) ---

    STATS = [
        StatSpec("Studies", "Statbar/Studies_Cnt"),
        StatSpec("Participants", "Statbar/Participants_Cnt"),
        StatSpec("Samples", "Statbar/Samples_Cnt"),
        StatSpec("Files", "Statbar/Files_Cnt"),
    ]

    # --- Home page verification ---

    def verify_home_page(self):
        """Verify Home copy/links from HomePage, plus the search and signup controls.

        Open Home explicitly so this check is independent of the configured landing
        route. Expected copy and URLs stay in CCDI_StaticData.xlsx, not Python.
        Links are inspected in place; signup is never submitted.
        """
        self.goto("home")
        self.accept_banner()
        self.verify_static_data("HomePage")
        self._verify_home_controls()

    def _verify_home_controls(self):
        """Record missing or disabled Home inputs without stopping other checks."""
        for obj in ("HeaderSearchInput", "FooterEmailInput", "FooterSignUpButton"):
            key = f"Static/HomePage/{obj}"
            el = self.ui.loc(self.repo.xpath(key)).first
            try:
                el.wait_for(state="visible", timeout=10000)
                if not el.is_enabled():
                    self._fail(f"Home control '{obj}' is disabled")
                    continue
                if obj.endswith("Input") and not el.is_editable():
                    self._fail(f"Home control '{obj}' is not editable")
                    continue
                self.results.append({"check": f"Home control {obj}", "status": "PASSED", "detail": ""})
            except PlaywrightError as err:
                self._fail(f"Home control '{obj}' is not available: {err}")

    # --- Navigation ---

    def open_explore(self):
        """Explore menu → C3DC Explore Participants (not a CCDI explore URL)."""
        self.click(
            "Navbar/Explore_Menu",
            ui_message="C3DC Explore Participants opened from CCDI Explore.",
        )
