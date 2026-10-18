"""C3DC (Clinical Commons Data Commons): https://clinicalcommons.ccdi.cancer.gov"""
import re
import time
from typing import Dict, List, Optional
from urllib.parse import quote

from Commons import action_log
from Commons.apps.base import BaseApp, StatSpec, TabSpec
from Commons.compare import compare_counts
from Commons.object_repository import FilterGroup, LocatorNotFound


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


# Object-repository filter group -> Explore Participants URL query key (see dashTemplate.queryParams).
FILTER_GROUP_TO_PARAM: Dict[str, str] = {
    "Study/dbGaP_Accession": "dbgap_accession",
    "Study/StudyName": "study_name",
    "Demographics/SexAtBirth": "sex_at_birth",
    "Demographics/Race": "race",
    "Diagnosis/Diagnosis": "diagnosis",
    "Diagnosis/AnatomicSite": "diagnosis_anatomic_site",
    "Diagnosis/DiagsClasifctnSystem": "diagnosis_classification_system",
    "Diagnosis/DiagnosisBasis": "diagnosis_basis",
    "Diagnosis/DiseasePhase": "disease_phase",
    "Survival/FirstEvent": "first_event",
    "Survival/LastKnownSurStatus": "last_known_survival_status",
    "Survival/CauseOfDeath": "cause_of_death",
    "Treatment/TreatmentAgent": "treatment_agent",
    "Treatment/TreatmentType": "treatment_type",
    "TreatmentResp/Response": "response",
    "TreatmentResp/RespCategory": "response_category",
    "TreatmentResp/RespSystem": "response_system",
    "Samples/AnatomicSite": "sample_anatomic_site",
    "Samples/SampleTumorStatus": "sample_tumor_status",
    "Samples/SampleTumorClassification": "tumor_spatial_extent",
}

class C3DC(BaseApp):
    NAME = "C3DC"
    BANNER_KEYS = ["HomePage/WarningBan_Continue_Btn"]
    STATIC_DATA_EXCEL = "C3DC_StaticData.xlsx"
    EXPLORE_PATH = "exploreParticipants"

    # Visible text on result tabs — Katalon selectTab('Participants', 10), etc.
    TAB_SELECT_LABELS: Dict[str, List[str]] = {
        "GeneticAnalysis": ["Genetic Analyses", "Genetic Analysis"],
        "Treatment": ["Treatments", "Treatment"],
        "TreatmentResp": ["Treatment Responses", "Treatment Response"],
    }
    # verify_tab() labels in tests → TABS keys (UI text / legacy names).
    TAB_VERIFY_ALIASES: Dict[str, str] = {
        "Genetic Analysis": "GeneticAnalysis",
        "Genetic Analyses": "GeneticAnalysis",
        "Treatments": "Treatment",
        "Treatment Responses": "TreatmentResp",
        "Treatment Response": "TreatmentResp",
        "Treatment Reponses": "TreatmentResp",
    }
    # Standard tab order after read_statbar() (matches Explore Participants UI labels).
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
    # Katalon TestRunner.selectTab — bar tabs, then More( N ) popover.
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

    # Explore Participants stat bar order (Katalon readStatBarC3DC / validateStatBar).
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url_filters: Dict[str, List[str]] = {}

    def load_query_file(self, file_name: str):
        qf = super().load_query_file(file_name)
        self._url_filters.clear()
        return qf

    def open_explore(self):
        """Open Explore Participants (replaces legacy Explore tab)."""
        action_log.say(f"open_explore -> /{self.EXPLORE_PATH}")
        self.goto(self.EXPLORE_PATH)
        self.page.locator("#statsbar_count_1").first.wait_for(state="visible", timeout=self.ui.timeout_ms)

    def select_filter(self, group: str, value: str):
        param = FILTER_GROUP_TO_PARAM.get(group)
        if not param:
            super().select_filter(group, value)
            return
        url_value = self._url_filter_value(group, value)
        bucket = self._url_filters.setdefault(param, [])
        if url_value not in bucket:
            bucket.append(url_value)
        action_log.say(f"select_filter (URL) group={group!r} value={value!r} -> {param}={url_value!r}")
        self._navigate_with_url_filters()

    def _navigate_with_url_filters(self):
        query = "&".join(
            f"{quote(k, safe='')}={'|'.join(quote(v, safe='') for v in vals)}"
            for k, vals in sorted(self._url_filters.items())
        )
        path = self.EXPLORE_PATH + (f"?{query}" if query else "")
        self.goto(path)
        self.page.locator("#statsbar_count_1").first.wait_for(state="visible", timeout=self.ui.timeout_ms)
        self.page.wait_for_timeout(500)

    @staticmethod
    def _facet_value_from_checkbox(group: FilterGroup, checkbox_xpath: str) -> Optional[str]:
        dd = group.dropdown
        if not dd:
            return None
        m = re.search(r'@id\s*=\s*["\']([^"\']+)["\']', dd)
        if not m:
            return None
        facet_id = m.group(1)
        id_m = re.search(r'checkbox_([^"\']+)', checkbox_xpath)
        if not id_m:
            return None
        rest = id_m.group(1)
        prefix = f"{facet_id}_"
        if rest.startswith(prefix):
            return rest[len(prefix):]
        return None

    def _url_filter_value(self, group: str, value: str) -> str:
        try:
            g = self.repo.filter_group(group)
            xp = g.checkbox_xpath(value)
            parsed = self._facet_value_from_checkbox(g, xp)
            if parsed is not None:
                return parsed
        except LocatorNotFound:
            pass
        return value

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
            return True

        more_xp = self.MORE_TABS_BTN_XP
        ui.wait_visible(more_xp, timeout_ms=int(timeout_s * 1000))
        ui.scroll_into_view(more_xp)
        self.page.wait_for_timeout(400)
        ui.js_click(more_xp, repo_key="ResultTabs/More_Tabs-Btn")

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
                return True
            self.page.wait_for_timeout(250)

        return False

    def verify_statbar(self):
        """Match Katalon C3DC: Memgraph stat row is Studies, Participants, Samples, Files by column index."""
        if self._stat_checked:
            return
        self._stat_checked = True
        expected = self.source.fetch_stat_bar_table(self.query_file)
        if not expected.rows:
            self._fail("Stat bar: the StatQuery returned no rows")
            return
        exp_row = expected.rows[0]
        by_header = {}
        if expected.header:
            by_header = {
                str(h).strip(): exp_row[i]
                for i, h in enumerate(expected.header)
                if i < len(exp_row)
            }
        exp = {}
        for i, spec in enumerate(self.STATS):
            if spec.name in by_header:
                exp[spec.name] = by_header[spec.name]
            elif i < len(exp_row):
                exp[spec.name] = exp_row[i]
        cmp = compare_counts(self.stats, exp)
        self._record("StatBar", cmp, ui_count=len(self.stats), exp_count=len(exp))

    def _open_from_more_menu(self, spec: TabSpec):
        """Fallback if BaseApp.open_tab is used — same as Katalon selectTab + More menu."""
        self.open_tab(spec.name)
