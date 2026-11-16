"""
C3DC (Clinical Commons Data Commons): https://clinicalcommons.ccdi.cancer.gov

Explore Participants: stat bar + result tabs (incl. More menu). Studies catalog: studies.py.
Expected data: Memgraph Cypher in InputFiles/C3DC/TC*.xlsx.
"""
import re
import time
from typing import Dict, List, Optional

from Commons import action_log
from Commons.base_app import BaseApp, StatSpec, TabSpec
from Commons.table_reader import resolve_table_body_xpath

# ---------------------------------------------------------------------------
# Tab wiring (workbook TabQuery keys ↔ ResultTabs locators)
# ---------------------------------------------------------------------------


def _tab(name, label, input_tab, stat, ui, db, max_pages=2):
    return TabSpec(
        name=name,
        tab=f"ResultTabs/{name}-Tab",
        table=f"ResultTabs/{name}-Tbl",
        header=f"ResultTabs/{name}-TblHdr",
        next="ResultTabs/All_Tabs_Next-Btn",
        input_tab=input_tab, stat=stat, ui_sheet=ui, db_sheet=db,
        max_pages=max_pages, label=label,
    )


# ---------------------------------------------------------------------------
# App adapter
# ---------------------------------------------------------------------------


class C3DC(BaseApp):
    NAME = "C3DC"
    BANNER_KEYS = ["Navbar/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "C3DC_StaticData.xlsx"
    EXPLORE_PATH = "exploreParticipants"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active_study_accession: Optional[str] = None

    # -----------------------------------------------------------------------
    # Tab names (UI labels vs TABS keys; Katalon selectTab)
    # -----------------------------------------------------------------------

    TAB_SELECT_LABELS: Dict[str, List[str]] = {
        "GeneticAnalysis": ["Genetic Analyses", "Genetic Analysis"],
        "Treatment": ["Treatments", "Treatment"],
        "TreatmentResp": ["Treatment Responses", "Treatment Response"],
    }

    TAB_VERIFY_ALIASES: Dict[str, str] = {
        "Genetic Analysis": "GeneticAnalysis",
        "Genetic Analyses": "GeneticAnalysis",
        "Treatments": "Treatment",
        "Treatment Responses": "TreatmentResp",
        "Treatment Response": "TreatmentResp",
        "Treatment Reponses": "TreatmentResp",
    }

    STANDARD_VERIFY_TABS: tuple = (
        "Participants",
        "Studies",
        "Diagnosis",
        "Genetic Analysis",
        "Treatments",
        "Treatment Responses",
        "Survival",
        "Samples",
    )

    RESULT_TAB_BUTTONS_XP = "//button[@role='tab']"
    MORE_TABS_BTN_XP = (
        "(//button[@role='tab'])[last()]/following::button"
        "[contains(@class,'more-button') or contains(normalize-space(.),'More')][1]"
    )
    MORE_MENU_ITEM_XP = "//div[contains(@class,'popover-list-item')]"
    _MORE_MENU_ITEM_TEXT_JS = """
(el) => {
  const s = el.querySelector('span[class*="popover-tab-name"]');
  return (s ? s.textContent : el.textContent) || '';
}
"""

    # -----------------------------------------------------------------------
    # Stat bar and result tabs
    # -----------------------------------------------------------------------

    STATS = [
        StatSpec("Studies", "Statbar/Studies-Count"),
        StatSpec("Participants", "Statbar/Participants-Count"),
        StatSpec("Samples", "Statbar/Samples-Count"),
        StatSpec("Files", "Statbar/Files-Count"),
    ]

    TABS = {
        "Studies":         _tab("Studies", "Studies", "StudiesTab", "Studies",
                                "UI_Studies", "DB_Studies"),
        "Participants":    _tab("Participants", "Participants", "ParticipantsTab", "Participants",
                                "UI_Participants", "DB_Participants"),
        "Diagnosis":       _tab("Diagnosis", "Diagnosis", "DiagnosisTab", "Participants",
                                "UI_Diagnosis", "DB_Diagnosis"),
        "GeneticAnalysis": _tab("GeneticAnalysis", "Genetic Analyses", "GeneticAnalysisTab", "Participants",
                                "UI_GeneticAnalysis", "DB_GeneticAnalysis"),
        "Treatment":       _tab("Treatment", "Treatments", "TreatmentTab", "Participants",
                                "UI_Treatment", "DB_Treatment"),
        "TreatmentResp":   _tab("TreatmentResp", "Treatment Responses", "TreatmentRespTab", "Participants",
                                "UI_TreatmentResp", "DB_TreatmentResp"),
        "Survival":        _tab("Survival", "Survival", "SurvivalTab", "Participants",
                                "UI_Survival", "DB_Survival"),
        "Samples":         _tab("Samples", "Samples", "SamplesTab", "Participants",
                                "UI_Samples", "DB_Samples"),
    }

    # -----------------------------------------------------------------------
    # Explore navigation
    # -----------------------------------------------------------------------

    def open_explore(self):
        """Open Explore Participants via navbar (Katalon: clickTab Explore-Tab)."""
        action_log.say("open_explore (Navbar/Explore-Tab)")
        self._active_study_accession = None
        self.click("Navbar/Explore-Tab", ui_message="Explore Participants opened successfully.")
        self._wait_explore_results_ready()

    def select_filter(self, group: str, value: str):
        """Apply filters via left-panel facet UI (expand, dropdown, checkbox click)."""
        super().select_filter(group, value)
        if group == "Study/dbGaP_Accession":
            self._active_study_accession = value
        self._wait_explore_results_ready()

    # -----------------------------------------------------------------------
    # Sync UI after filters (stat bar + participant grid)
    # -----------------------------------------------------------------------

    def _wait_explore_results_ready(self):
        self.page.locator("#statsbar_count_1").first.wait_for(state="visible", timeout=self.ui.timeout_ms)
        self.ui.stable_text(
            self.repo.xpath("Statbar/Participants-Count"),
            settle_s=0.75,
            timeout_s=30,
            label="participants_stat",
        )
        self.ui.wait_idle()
        self._wait_participant_table_for_study()

    def _wait_participant_table_for_study(self, timeout_s: float = 30.0) -> None:
        """After filters, the grid can lag the stat bar; require visible rows to match the study filter."""
        acc = self._active_study_accession
        if not acc:
            return
        tbl = self.repo.xpath("ResultTabs/Participants-Tbl")
        tbl_bdy = resolve_table_body_xpath("C3DC", tbl)
        end = time.time() + timeout_s
        while time.time() < end:
            ok = self.page.evaluate(
                """({ bodyXp, acc }) => {
                  const r = document.evaluate(bodyXp, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                  const tb = r.singleNodeValue;
                  if (!tb) return false;
                  const rows = tb.querySelectorAll(':scope > tr');
                  if (!rows.length) return false;
                  for (const tr of rows) {
                    const cells = Array.from(tr.querySelectorAll(':scope > td'))
                      .map(td => (td.innerText || '').replace(/\\s+/g, ' ').trim());
                    const phs = cells.filter(t => /^phs\\d+$/.test(t));
                    if (!phs.length) return false;
                    if (phs.some(t => t !== acc)) return false;
                  }
                  return true;
                }""",
                {"bodyXp": tbl_bdy, "acc": acc},
            )
            if ok:
                action_log.ui_action(f"Participant table shows study {acc} on all visible rows.")
                return
            time.sleep(0.25)
        raise TimeoutError(
            f"Participant table did not show only study {acc!r} within {timeout_s}s "
            "(study filter may not have applied)."
        )

    # -----------------------------------------------------------------------
    # Tab label matching (bar + More menu)
    # -----------------------------------------------------------------------

    @staticmethod
    def _normalize_tab_label(raw: str) -> str:
        return re.sub(r"\s+", " ", (raw or "").replace("\u00a0", " ")).strip()

    @classmethod
    def _tab_label_prefix_matches(cls, label: str, name: str) -> bool:
        if not name or label is None:
            return False
        if label.lower() == name.lower():
            return True
        if len(label) <= len(name):
            return False
        if label[: len(name)].lower() != name.lower():
            return False
        return not label[len(name)].isalnum()

    @classmethod
    def _tab_name_candidates(cls, option_text: str) -> List[str]:
        """UI/search strings for one tab (singular/plural and More-menu labels)."""
        seen: set = set()
        out: List[str] = []

        def add(text: str) -> None:
            norm = cls._normalize_tab_label(text)
            if norm and norm not in seen:
                seen.add(norm)
                out.append(norm)

        add(option_text)
        key = cls.TAB_VERIFY_ALIASES.get(option_text) or cls.TAB_VERIFY_ALIASES.get(
            cls._normalize_tab_label(option_text)
        )
        if key:
            spec = cls.TABS.get(key)
            if spec and spec.label:
                add(spec.label)
            for alt in cls.TAB_SELECT_LABELS.get(key, []):
                add(alt)
        return out

    @classmethod
    def _tab_label_matches(cls, raw: str, option_text: str) -> bool:
        label = cls._normalize_tab_label(raw)
        core = re.sub(r"\s*\([\d,]+\)\s*$", "", label).strip()
        for lbl in (label, core) if core != label else (label,):
            lbl_ns = re.sub(r"\s+", "", lbl)
            for candidate in cls._tab_name_candidates(option_text):
                name = cls._normalize_tab_label(candidate)
                if cls._tab_label_prefix_matches(lbl, name):
                    return True
                name_ns = re.sub(r"\s+", "", name)
                if cls._tab_label_prefix_matches(lbl_ns, name_ns):
                    return True
        return False

    # -----------------------------------------------------------------------
    # verify_tab / selectTab / open_tab
    # -----------------------------------------------------------------------

    def verify_tab(self, name: str):
        name = self.TAB_VERIFY_ALIASES.get(name, name)
        super().verify_tab(name)

    def select_tab(self, option_text: str, timeout_s: int = 10):
        """Katalon: TestRunner.selectTab(optionText, timeout)."""
        action_log.say(f"selectTab {option_text!r} timeout={timeout_s}s")
        if not self._select_result_tab(option_text, timeout_s=timeout_s):
            raise RuntimeError(
                f"Result tab {option_text!r} was not on the tab bar or in the More menu."
            )
        self.ui.wait_idle()

    def _tab_select_labels(self, name: str, spec: TabSpec) -> List[str]:
        labels = list(self.TAB_SELECT_LABELS.get(name, []))
        primary = spec.label or name
        if primary not in labels:
            labels.insert(0, primary)
        return labels

    def open_tab(self, name: str):
        """Open a result tab by framework name (uses Katalon selectTab logic)."""
        spec = self.TABS[name]
        action_log.say(f"openTab {name!r}")
        for label in self._tab_select_labels(name, spec):
            if self._select_result_tab(label):
                self.ui.wait_idle()
                return
        raise RuntimeError(
            f"Could not open C3DC result tab {name!r} (tried labels "
            f"{self._tab_select_labels(name, spec)!r})."
        )

    @staticmethod
    def _is_more_tab_button(raw: str, class_name: str = "") -> bool:
        if "more-button" in (class_name or ""):
            return True
        return bool(re.match(r"^:?\s*More\b", (raw or "").strip(), re.I))

    def _select_result_tab(self, label: str, timeout_s: int = 10) -> bool:
        """TestRunner.selectTab: visible bar tabs, then More popover (Survival, Samples, …)."""
        ui = self.ui
        tab_xp = self.RESULT_TAB_BUTTONS_XP
        ui.wait_visible(f"({tab_xp})[1]", timeout_ms=int(timeout_s * 1000))
        ui.scroll_into_view(f"({tab_xp})[1]")

        for i in range(ui.loc(tab_xp).count()):
            nth = f"({tab_xp})[{i + 1}]"
            loc = ui.loc(nth)
            raw = loc.evaluate("el => el.textContent") or ""
            cls = loc.evaluate("el => el.className") or ""
            if self._is_more_tab_button(raw, cls):
                continue
            if not self._tab_label_matches(raw, label):
                continue
            ui.scroll_into_view(nth)
            ui.js_click(nth, repo_key=f"ResultTabs/selectTab-{label}")
            action_log.ui_action(f"Result tab opened successfully: {label}.")
            return True

        more_xp = self.MORE_TABS_BTN_XP
        ui.wait_visible(more_xp, timeout_ms=int(timeout_s * 1000))
        ui.scroll_into_view(more_xp)
        self.page.wait_for_timeout(400)
        ui.js_click(more_xp, repo_key="ResultTabs/More_Tabs-Btn")
        action_log.ui_action("More tabs menu opened successfully.")

        deadline = time.time() + timeout_s
        menu_xp = self.MORE_MENU_ITEM_XP
        while time.time() < deadline:
            n_items = ui.loc(menu_xp).count()
            for i in range(n_items):
                item_xp = f"({menu_xp})[{i + 1}]"
                raw = ui.loc(item_xp).evaluate(self._MORE_MENU_ITEM_TEXT_JS)
                if not self._tab_label_matches(raw, label):
                    continue
                ui.js_click(item_xp)
                action_log.ui_action(f"Result tab opened successfully: {label}.")
                return True
            self.page.wait_for_timeout(250)

        return False

    def _open_from_more_menu(self, spec: TabSpec):
        """Fallback if BaseApp.open_tab is used — same as Katalon selectTab + More menu."""
        self.open_tab(spec.name)

    # -----------------------------------------------------------------------
    # Studies catalog (/studies — see studies.py)
    # -----------------------------------------------------------------------

    def open_studies_listing(self):
        """Open the /studies catalog (not Explore Participants → Studies)."""
        from Commons.apps.c3dc.studies import open_studies_listing

        open_studies_listing(self)

    def verify_studies_listing(self):
        """Compare /studies catalog rows to StudiesListingTab Cypher. Does not call verify_tab."""
        from Commons.apps.c3dc.studies import verify_studies_listing

        verify_studies_listing(self)

    # -----------------------------------------------------------------------
    # Study details and reports (study_details.py)
    # -----------------------------------------------------------------------

    def open_study_details(self, accession: str):
        """Click an accession in the catalog; preserve its row for comparison."""
        from Commons.apps.c3dc.study_details import open_study_details

        open_study_details(self, accession)

    def begin_study_details_report(self, report_name: str = "StudyDetails_AllStudies"):
        """Start a fresh consolidated report for this study-details testcase."""
        from Commons.apps.c3dc.study_details import begin_study_details_report

        begin_study_details_report(self, report_name)

    def verify_study_details(self, accession: str):
        """Check study accession, name, description, counts and manifest download."""
        from Commons.apps.c3dc.study_details import verify_study_details

        verify_study_details(self, accession)

    # -----------------------------------------------------------------------
    # Cohorts (shared popup helpers live in cohort.py)
    # -----------------------------------------------------------------------

    def create_cohort_from_all_participants(self):
        """Create a cohort containing every participant in the current filtered results."""
        from Commons.apps.c3dc.cohort import create_cohort_from_all_participants

        create_cohort_from_all_participants(self)

    def verify_cohort_created(self):
        """Check the new cohort's popup, participant count, unique rows and study."""
        from Commons.apps.c3dc.cohort import verify_cohort_created

        return verify_cohort_created(self)

    # -----------------------------------------------------------------------
    # Adding participants to an existing cohort
    # -----------------------------------------------------------------------

    def remember_cohort_for_addition(self):
        """Capture the current cohort before changing the participant filters."""
        from Commons.apps.c3dc.cohort import remember_cohort_for_addition
        remember_cohort_for_addition(self)

    def replace_cohort_filter(self, group, previous_value, replacement_value):
        """Replace a filter while preserving the current cohort."""
        from Commons.apps.c3dc.cohort import replace_cohort_filter
        replace_cohort_filter(self, group, previous_value, replacement_value)

    def add_all_participants_to_existing_cohort(self):
        """Choose the existing cohort and add all currently filtered participants."""
        from Commons.apps.c3dc.cohort import add_all_participants_to_existing_cohort
        add_all_participants_to_existing_cohort(self)

    def add_selected_participants_to_existing_cohort(self):
        """Add only the checked participant page to the remembered cohort."""
        from Commons.apps.c3dc.cohort import add_selected_participants_to_existing_cohort
        add_selected_participants_to_existing_cohort(self)

    def verify_participants_added_to_cohort(self, report_name='cohort_addition'):
        """Verify persisted membership and count against the union of both sets."""
        from Commons.apps.c3dc.cohort import verify_participants_added_to_cohort
        verify_participants_added_to_cohort(self, report_name)

    # -----------------------------------------------------------------------
    # Cohort popup navigation
    # -----------------------------------------------------------------------

    def open_cohorts(self):
        """Open View All Cohorts using the page control."""
        from Commons.apps.c3dc.cohort import open_cohorts
        return open_cohorts(self)

    def close_cohorts(self):
        """Close the cohort popup without editing its contents."""
        from Commons.apps.c3dc.cohort import close_cohorts
        close_cohorts(self)

    # -----------------------------------------------------------------------
    # Cohort duplication
    # -----------------------------------------------------------------------

    def duplicate_selected_cohort(self):
        """Duplicate the currently selected cohort in the management popup."""
        from Commons.apps.c3dc.cohort import duplicate_selected_cohort
        duplicate_selected_cohort(self)

    def verify_duplicate_cohort_created(self):
        """Verify the copy's data and ensure the source cohort is unchanged."""
        from Commons.apps.c3dc.cohort import verify_duplicate_cohort_created
        return verify_duplicate_cohort_created(self)

    # -----------------------------------------------------------------------
    # Participant selection and selected-participant cohorts
    # -----------------------------------------------------------------------

    def verify_selected_participants_option(self, state):
        """Check the Create New Cohort menu before and after participant selection."""
        from Commons.apps.c3dc.cohort import verify_selected_participants_option
        verify_selected_participants_option(self, state)

    def select_participant_page(self, page_number):
        """Select a visible results page and remember its participant/study IDs."""
        from Commons.apps.c3dc.cohort import select_participant_page
        select_participant_page(self, page_number)

    def select_next_participant_page_only(self):
        """Clear the previous page's selection and select the next page only."""
        from Commons.apps.c3dc.cohort import select_next_participant_page_only
        select_next_participant_page_only(self)

    def create_cohort_from_selected_participants(self):
        """Create a cohort from the participants selected across results pages."""
        from Commons.apps.c3dc.cohort import create_cohort_from_selected_participants
        create_cohort_from_selected_participants(self)

    # -----------------------------------------------------------------------
    # Repeated duplication and cohort creation limit
    # -----------------------------------------------------------------------

    def duplicate_cohort_repeatedly(self, count):
        """Duplicate and verify the selected cohort a requested number of times."""
        from Commons.apps.c3dc.cohort import duplicate_cohort_repeatedly
        duplicate_cohort_repeatedly(self, count)

    def verify_duplicate_cohort_limit(self):
        """Verify the 20-cohort boundary and disabled Duplicate controls."""
        from Commons.apps.c3dc.cohort import verify_duplicate_cohort_limit
        verify_duplicate_cohort_limit(self)

    # -----------------------------------------------------------------------
    # Cohort name and description editing
    # -----------------------------------------------------------------------

    def update_cohort_details(self, name, description):
        """Edit the selected cohort's name and description without saving yet."""
        from Commons.apps.c3dc.cohort import update_cohort_details
        update_cohort_details(self, name, description)

    # -----------------------------------------------------------------------
    # Cohort removal confirmations and deletion
    # -----------------------------------------------------------------------

    def verify_cohort_removal_confirmation(self, target, expected_message):
        """Verify the warning, cancellation, and confirmed cohort deletion."""
        from Commons.apps.c3dc.cohort import verify_cohort_removal_confirmation
        verify_cohort_removal_confirmation(self, target, expected_message)

    # -----------------------------------------------------------------------
    # Manifest CSV download and verification
    # -----------------------------------------------------------------------

    def download_cohort_manifest(self, report_name="cohort_manifest"):
        """Save the selected cohort's CSV in this environment's output folder."""
        from Commons.apps.c3dc.cohort import download_cohort_manifest
        return download_cohort_manifest(self, report_name)

    def verify_cohort_manifest(self):
        """Compare unique participant/study IDs in the saved CSV with the cohort."""
        from Commons.apps.c3dc.cohort import verify_cohort_manifest
        verify_cohort_manifest(self)

    # -----------------------------------------------------------------------
    # Metadata JSON download and verification
    # -----------------------------------------------------------------------

    def download_cohort_metadata(self, report_name="cohort_metadata"):
        """Save the selected cohort's Metadata JSON in the output folder."""
        from Commons.apps.c3dc.cohort import download_cohort_metadata
        return download_cohort_metadata(self, report_name)

    def verify_cohort_metadata(self):
        """Validate the downloaded JSON hierarchy and selected cohort membership."""
        from Commons.apps.c3dc.cohort import verify_cohort_metadata
        verify_cohort_metadata(self)

    # -----------------------------------------------------------------------
    # Cohort control tooltips
    # -----------------------------------------------------------------------

    def verify_cohort_tooltip(self, control, expected_text):
        """Hover a cohort control and verify the expected tooltip copy."""
        from Commons.apps.c3dc.cohort import verify_cohort_tooltip
        verify_cohort_tooltip(self, control, expected_text)

    # -----------------------------------------------------------------------
    # Save and verify persisted cohort changes
    # -----------------------------------------------------------------------

    def save_cohort_changes(self):
        """Click Save Changes for the current cohort metadata edit."""
        from Commons.apps.c3dc.cohort import save_cohort_changes
        save_cohort_changes(self)

    def verify_cohort_details_saved(self):
        """Verify saved metadata and unchanged membership after a page reload."""
        from Commons.apps.c3dc.cohort import verify_cohort_details_saved
        return verify_cohort_details_saved(self)

    # -----------------------------------------------------------------------
    # Cohort Analyzer (cohort_analyzer.py)
    # -----------------------------------------------------------------------

    def open_cohort_analyzer(self):
        """Open the analyzer through its navigation link."""
        from Commons.apps.c3dc.cohort_analyzer import open_cohort_analyzer
        open_cohort_analyzer(self)

    def add_example_cohorts(self):
        """Create the three example cohorts with a single button click."""
        from Commons.apps.c3dc.cohort_analyzer import add_example_cohorts
        add_example_cohorts(self)

    def verify_example_cohorts_created(self, expected_names):
        """Verify the example names, participant counts and selected states."""
        from Commons.apps.c3dc.cohort_analyzer import verify_example_cohorts_created
        verify_example_cohorts_created(self, expected_names)
