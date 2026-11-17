"""
C3DC (Clinical Commons Data Commons): https://clinicalcommons.ccdi.cancer.gov

Explore Participants: four result tabs. Explore Files: Files and Imaging Data.
Studies catalog: studies.py.
Expected data: Memgraph Cypher in InputFiles/C3DC/TC*.xlsx.
"""
import re
import json
from dataclasses import replace
from typing import Dict, List, Optional

from Commons import action_log
from Commons.base_app import BaseApp, StatSpec, TabSpec
from Commons.table_reader import active_result_tab_record_count

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
    }

    TAB_VERIFY_ALIASES: Dict[str, str] = {
        "Genetic Analysis": "GeneticAnalysis",
        "Genetic Analyses": "GeneticAnalysis",
        "Imaging Data": "ImagingData",
    }

    STANDARD_VERIFY_TABS: tuple = (
        "Participants",
        "Studies",
        "Genetic Analysis",
        "Samples",
    )

    EXPLORE_FILE_TABS: tuple = ("Files", "Imaging Data")

    RESULT_TAB_BUTTONS_XP = "//button[@role='tab']"
    # Older Excel cases can still request retired tabs; report them as skipped.
    RETIRED_RESULT_TABS = frozenset({
        "Diagnosis", "Treatment", "Treatments", "TreatmentResp",
        "Treatment Responses", "Treatment Response", "Treatment Reponses", "Survival",
    })

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
        "GeneticAnalysis": _tab("GeneticAnalysis", "Genetic Analyses", "GeneticAnalysisTab", "Participants",
                                "UI_GeneticAnalysis", "DB_GeneticAnalysis"),
        "Samples":         _tab("Samples", "Samples", "SamplesTab", "Participants",
                                "UI_Samples", "DB_Samples"),
        "Files": _tab("Files", "Files", "FilesTab", "Files", "UI_Files", "DB_Files"),
        "ImagingData": _tab("ImagingData", "Imaging Data", "ImagingDataTab", "Files",
                            "UI_ImagingData", "DB_ImagingData"),
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

    def open_explore_files(self):
        """Switch to Explore Files through the navbar, retaining the active filters."""
        self.click("Navbar/Explore-Files-Tab", ui_message="Explore Files opened successfully.")
        self._wait_explore_results_ready()

    def select_filter(self, group: str, value: str):
        """Apply filters via left-panel facet UI (expand, dropdown, checkbox click)."""
        checkbox = self.repo.filter_group(group).checkbox_xpath(value)
        match = re.search(r"@id\s*=\s*['\"]checkbox_([^'\"]+)['\"]", checkbox)
        selected_value = match.group(1).split("_", 1)[-1] if match else value

        def filtered_search(response):
            if "/v1/graphql" not in response.url:
                return False
            try:
                payload = json.loads(response.request.post_data or "{}")
            except (ValueError, TypeError):
                return False
            values = payload.get("variables", {}).values()
            return payload.get("operationName") == "search" and any(
                selected_value == item or isinstance(item, list) and selected_value in item
                for item in values
            )

        # The UI debounces filters. Waiting for its search response prevents
        # stable but outdated stat counts from being compared to the new cohort.
        with self.page.expect_response(filtered_search, timeout=self.ui.timeout_ms) as search:
            super().select_filter(group, value)
        search.value.body()
        if group == "Study/dbGaP_Accession":
            self._active_study_accession = value
        self._wait_explore_results_ready()

    def _expand_group(self, group, until_visible=None, checkbox=None):
        """Keep the Study panel open when applying another study filter."""
        if (group.key.startswith("Study/") and group.dropdown
                and self.ui.is_visible(group.dropdown)):
            # Sidebar category labels have no expanded state; clicking Study
            # again would close the panel that already contains this dropdown.
            group = replace(group, facet=None)
        return super()._expand_group(group, until_visible, checkbox)

    # -----------------------------------------------------------------------
    # Filter readiness (table data is read by explicit verification steps)
    # -----------------------------------------------------------------------

    def _wait_explore_results_ready(self):
        """Settle filter/stat updates; explicit verification steps read the table."""
        self.page.locator("#statsbar_count_1").first.wait_for(state="visible", timeout=self.ui.timeout_ms)
        self.ui.stable_text(
            self.repo.xpath("Statbar/Participants-Count"),
            settle_s=0.75,
            timeout_s=30,
            label="participants_stat",
        )
        self.ui.wait_idle()

    # -----------------------------------------------------------------------
    # Tab label matching
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
        """UI/search strings for one tab (singular/plural labels)."""
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
        if name in self.RETIRED_RESULT_TABS:
            detail = "result tab removed from C3DC Explore"
            action_log.ui_action(f"Skipped {name} tab ({detail}).")
            self.results.append({"check": name, "status": "SKIPPED", "detail": detail})
            return
        name = self.TAB_VERIFY_ALIASES.get(name, name)
        super().verify_tab(name)

    def prepare_tab_comparison(self, spec, ui_table, expected) -> None:
        if spec.name == "Studies":
            from Commons.apps.c3dc.table_cells import resolve_ranked_cells

            resolved = resolve_ranked_cells(ui_table, expected)
            if resolved:
                action_log.say(f"Validated {resolved} ranked cells, allowing equal-count ties.")
        if spec.name == "Files":
            from Commons.apps.c3dc.table_cells import resolve_file_name_aliases
            from Commons.compare import normalize_list

            # Shared files can list ages in any order. Canonicalize both lists
            # before the shared comparator can mistake a trailing age for a CPI badge.
            for table in (ui_table, expected):
                if "Age at Collection" in table.header:
                    column = table.header.index("Age at Collection")
                    for row in table.rows:
                        row[column] = normalize_list(row[column])

            resolved = resolve_file_name_aliases(ui_table, expected)
            if resolved:
                action_log.say(f"Validated {resolved} shared-file names against database aliases.")

    def select_tab(self, option_text: str, timeout_s: int = 10):
        """Katalon: TestRunner.selectTab(optionText, timeout)."""
        action_log.say(f"selectTab {option_text!r} timeout={timeout_s}s")
        if not self._select_result_tab(option_text, timeout_s=timeout_s):
            raise RuntimeError(
                f"Result tab {option_text!r} was not on the tab bar."
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
        # Keep an explicit column sort when verification reopens the selected tab.
        selected = self.ui.loc("//button[@role='tab' and @aria-selected='true']")
        if selected.count():
            current = selected.first.inner_text()
            if any(self._tab_label_matches(current, label)
                   for label in self._tab_select_labels(name, spec)):
                return
        action_log.say(f"openTab {name!r}")
        for label in self._tab_select_labels(name, spec):
            if self._select_result_tab(label):
                self.ui.wait_idle()
                return
        raise RuntimeError(
            f"Could not open C3DC result tab {name!r} (tried labels "
            f"{self._tab_select_labels(name, spec)!r})."
        )

    def sort_result_tab(self, name: str, column_key: str):
        """Use an explicit ascending UI sort before comparing a limited result page."""
        name = self.TAB_VERIFY_ALIASES.get(name, name)
        self.open_tab(name)
        if active_result_tab_record_count(self.ui) == 0:
            action_log.say(f"Skipped sorting {name}: the result tab has no records.")
            return
        column = self.repo.xpath(column_key)
        label = self.ui.loc(column)
        active = "MuiTableSortLabel-active" in (label.get_attribute("class") or "")
        ascending = label.locator("xpath=.//*[contains(@class,'iconDirectionAsc')]").count() > 0
        if not (active and ascending):
            self.ui.click(column, repo_key=column_key)
        self.ui.wait_visible(f"{column}//*[contains(@class,'iconDirectionAsc')]")
        # Sorting is debounced by the UI. Wait for actual ordered rows, not just its arrow.
        index = label.evaluate("el => el.closest('th').cellIndex")
        table = self.repo.xpath(self.TABS[name].table)
        self.page.wait_for_function(
            """({table, index}) => {
                const root = document.evaluate(table, document, null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                const values = Array.from(root?.querySelectorAll('tbody tr') || [])
                    .map(row => row.cells[index]?.innerText.trim() || '');
                return values.length > 0 && values.every((value, i) => !i || values[i - 1] <= value);
            }""",
            arg={"table": table, "index": index}, timeout=self.ui.timeout_ms,
        )
        self.ui.wait_idle()

    def _select_result_tab(self, label: str, timeout_s: int = 10) -> bool:
        """Select a visible result tab on the current Explore page."""
        ui = self.ui
        tab_xp = self.RESULT_TAB_BUTTONS_XP
        ui.wait_visible(f"({tab_xp})[1]", timeout_ms=int(timeout_s * 1000))
        ui.scroll_into_view(f"({tab_xp})[1]")

        for i in range(ui.loc(tab_xp).count()):
            nth = f"({tab_xp})[{i + 1}]"
            loc = ui.loc(nth)
            raw = loc.evaluate("el => el.textContent") or ""
            if not self._tab_label_matches(raw, label):
                continue
            ui.scroll_into_view(nth)
            ui.js_click(nth, repo_key=f"ResultTabs/selectTab-{label}")
            action_log.ui_action(f"Result tab opened successfully: {label}.")
            return True

        return False

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
