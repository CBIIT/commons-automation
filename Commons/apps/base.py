"""
BaseApp: the object every test talks to. One subclass per application (C3DC, CDS, ...).

Katalon (TestRunner.groovy)                      Here
------------------------------------------------ -----------------------------------------
RunKatalon('X.xlsx')                             app.load_query_file('X.xlsx')
clickTab('.../WarningBan_Continue_Btn')          app.accept_banner()
clickTab / clickTabCDSStat (filter ddn + chkbx)  app.select_filter('Study/dbGaP_Accession', 'phs000466')
readStatBarC3DC / readStatBarCDS                 app.read_statbar()
openTab + multiFunction(...)                     app.verify_tab('Participants')
validateStatBar                                  done inside verify_tab (once per case)
KeywordUtil.markFailed                           recorded in app.failures; test fails at the end
"""
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from Commons import action_log, excel_writer
from Commons.browser_actions import Ui
from Commons.compare import Comparison, compare_counts, compare_tables
from Commons.db_source import ExpectedDataSource, Table
from Commons.object_repository import FilterGroup, ObjectRepository
from Commons.settings import AppSettings, OUTPUT_ROOT, input_dir
from Commons.query_reader import QueryFile, read_query_file
from Commons.table_reader import active_result_tab_record_count, options_from_spec, read_table_data


@dataclass
class TabSpec:
    """Everything needed to read and check one result tab."""
    name: str                # short name used in tests, e.g. 'Participants'
    tab: str                 # locator key of the tab button
    table: str               # locator key of the table
    header: str              # locator key of the table header
    next: str                # locator key of the "next page" button
    input_tab: str           # row name in the input Excel, e.g. 'ParticipantsTab'
    stat: str                # stat bar item that tells us whether the tab has data
    ui_sheet: str            # worksheet in <case>_UI.xlsx (table read from the browser)
    db_sheet: str            # worksheet in <case>_DB.xlsx (table from expected-data source)
    max_pages: Optional[int] = None  # pages to read; None = BaseApp.MAX_PAGES
    first_page: int = 1      # 1-based page to start collecting after rewind to page 1
    first_child: bool = False  # read the cell's first child element (GC) instead of the cell
    label: str = ""          # text shown in the "More" popover, if the tab is hidden there


@dataclass
class StatSpec:
    name: str                # 'Participants'
    key: str                 # locator key
    use_html: bool = False   # Katalon read innerHTML for some apps, innerText for others


class BaseApp:
    NAME = ""
    TABS: Dict[str, TabSpec] = {}
    STATS: List[StatSpec] = []          # order = column order of the StatQuery result
    STAT_UI_SHEET = "StatOutput"        # Katalon WebExcel / UI workbook stat sheet
    STAT_DB_SHEET = "StatOutput"        # Katalon TsvExcel / DB workbook stat sheet
    BANNER_KEYS: List[str] = []
    STATIC_DATA_EXCEL = ""
    MAX_PAGES = int(os.environ.get("MAX_PAGES", "1000"))

    def __init__(self, page, settings: AppSettings, repo: ObjectRepository,
                 source: Optional[ExpectedDataSource], timeout_ms: int = 30000):
        self.page = page
        self.settings = settings
        self.repo = repo
        self.source = source
        self.ui = Ui(page, timeout_ms)
        self.query_file: Optional[QueryFile] = None
        self.stats: Dict[str, str] = {}
        self.failures: List[str] = []
        self.results: List[dict] = []
        self._stat_checked = False
        self.output_dir = OUTPUT_ROOT / settings.app / settings.env.upper()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ session
    def open(self):
        """WebUI.openBrowser + navigateToUrl."""
        action_log.navigate(self.settings.url)
        self.page.goto(self.settings.url, wait_until="domcontentloaded")
        self.ui.wait_idle()

    def goto(self, path: str):
        """Open another page of the same site, e.g. app.goto('resources') (Katalon: WebUI.navigateToUrl)."""
        from urllib.parse import urlsplit
        u = urlsplit(self.settings.url)
        url = f"{u.scheme}://{u.netloc}/{path.lstrip('/')}"
        action_log.navigate(url)
        self.page.goto(url, wait_until="domcontentloaded")
        self.ui.wait_idle()

    def accept_banner(self, timeout_ms: int = 8000):
        """Click Continue on the warning banner if it shows up (it does on every fresh load)."""
        for key in self.BANNER_KEYS:
            xp = self.repo.xpath(key)
            try:
                self.ui.visible(xp).first.wait_for(state="visible", timeout=timeout_ms)
                self.ui.click(xp, repo_key=key)
                self.ui.loc(xp).first.wait_for(state="hidden", timeout=5000)
                action_log.ui_action("Warning banner dismissed successfully.")
                return
            except Exception:
                continue

    def load_query_file(self, file_name: str) -> QueryFile:
        """Load the test query workbook from InputFiles/<app>/."""
        action_log.say(f"load_query_file: {file_name}")
        self.query_file = read_query_file(self.NAME, file_name, input_dir(self.NAME))
        self.stats.clear()
        self._stat_checked = False
        return self.query_file

    # ------------------------------------------------------------------ generic clicks
    def click(self, key: str, ui_message: Optional[str] = None):
        """Click any element by its object-repository key, e.g. 'Navbar/Explore-Tab'."""
        self.ui.click(self.repo.xpath(key), repo_key=key)
        self.ui.wait_idle()
        if ui_message:
            action_log.ui_action(ui_message)

    # ------------------------------------------------------------------ filters
    def select_filter(self, group: str, value: str):
        """Tick one checkbox in a filter facet, e.g. select_filter('Study/dbGaP_Accession', 'phs000466').

        Opens the facet and its list only if they are not already open, scrolls a long list to the
        checkbox, and waits for the result counts to reload.
        """
        g: FilterGroup = self.repo.filter_group(group)
        chk = g.checkbox_xpath(value)
        ui = self.ui
        action_log.say(f"select_filter group={group!r} value={value!r}")

        if g.search:
            if not ui.is_visible(g.search):
                self._expand_group(g, checkbox=chk)
            ui.fill(g.search, self._search_text(chk, value), repo_key=f"{group}/search")
            ui.wait_idle(3000)
        else:
            # Katalon: click facet accordion, then sub-filter dropdown, then checkbox.
            self._expand_group(g, until_visible=chk, checkbox=chk)

        if not ui.is_visible(chk):
            header = g.dropdown_for(chk) or g.facet
            if header and ui.is_present(header):
                ui.scroll_facet_until_visible(header, chk)
        ui.click(chk, repo_key=f"{group}/{value}")
        ui.wait_idle()
        self.page.wait_for_timeout(500)
        action_log.ui_action(self._filter_checkbox_message(group, value))

    @staticmethod
    def _filter_checkbox_message(group: str, value: str) -> str:
        if group.startswith("Study/") and "Accession" in group:
            return f"Study {value} selected successfully."
        facet = action_log.filter_facet_display(group)
        return f"{value} checkbox clicked successfully ({facet})."

    def _expand_group(self, g: FilterGroup, until_visible: Optional[str] = None, checkbox: Optional[str] = None):
        """Open left-panel facet, then sub-filter dropdown (Katalon clickTab *Facet / *-Ddn)."""
        ui = self.ui
        dropdown = g.dropdown_for(checkbox) if checkbox else g.dropdown
        facet_label = g.facet_key or g.key.split("/")[0]
        facet_repo = f"{g.key}/facet" if g.facet else None

        if g.facet and ui.is_present(g.facet):
            ui.scroll_into_view(g.facet)
            ui.js_click(g.facet, repo_key=facet_repo or f"{facet_label}_Facet")
            ui.wait_idle(500)
            self.page.wait_for_timeout(400)
            facet_name = action_log.filter_facet_display(g.key, g.facet_key)
            action_log.ui_action(f"{facet_name} facet opened successfully.")

        if not dropdown:
            return
        if until_visible and ui.is_visible(until_visible):
            return

        try:
            ui.wait_visible(dropdown, timeout_ms=15000)
        except Exception:
            pass
        if until_visible and ui.is_visible(until_visible):
            return
        if ui.is_present(dropdown):
            ui.js_click(dropdown, repo_key=f"{g.key}/dropdown")
            self.page.wait_for_timeout(400)
            sub = action_log.filter_subfilter_display(g.key)
            action_log.ui_action(f"{sub} filter dropdown opened successfully.")
            if until_visible:
                try:
                    ui.wait_visible(until_visible, timeout_ms=15000)
                except Exception:
                    pass

    @staticmethod
    def _search_text(checkbox_xpath: str, value: str) -> str:
        """Text to type in a facet's search box: the value part of the checkbox id (…checkbox_<Facet>_<Value>)."""
        m = re.search(r"checkbox_[^_\"']+_(.+?)[\"']\]", checkbox_xpath)
        return m.group(1) if m else value

    # ------------------------------------------------------------------ stat bar
    def read_statbar(self) -> Dict[str, str]:
        """Read the counts shown in the stat bar (after filters are applied)."""
        self.ui.wait_idle()
        values = self.ui.stable_texts([(self.repo.xpath(s.key), s.use_html) for s in self.STATS])
        for s, raw in zip(self.STATS, values):
            self.stats[s.name] = raw.replace(",", "").strip()
            action_log.stat_bar_count_from_ui(s.name, self.stats[s.name])
        action_log.stat_bar(dict(self.stats))
        action_log.ui_action(f"Stat bar read: {dict(self.stats)}")
        self._stat_checked = False
        return dict(self.stats)

    def _stat_value(self, name: str) -> int:
        try:
            return int(self.stats.get(name, "0") or 0)
        except ValueError:
            return 0

    def _expected_stat_dict(self, expected: Table) -> Dict[str, str]:
        """Map StatQuery result row to stat-bar names (Studies, Participants, …)."""
        if not expected.rows:
            return {}
        exp_row = expected.rows[0]
        by_header: Dict[str, str] = {}
        if expected.header:
            by_header = {
                str(h).strip(): exp_row[i]
                for i, h in enumerate(expected.header)
                if i < len(exp_row)
            }
        exp: Dict[str, str] = {}
        for i, spec in enumerate(self.STATS):
            if spec.name in by_header:
                exp[spec.name] = by_header[spec.name]
                continue
            lower = spec.name.lower()
            key = next((k for k in by_header if k.lower() == lower), None)
            if key is not None:
                exp[spec.name] = by_header[key]
            elif i < len(exp_row):
                exp[spec.name] = exp_row[i]
        return exp

    def verify_statbar(self):
        """Compare stat bar UI vs StatQuery (Katalon validateStatBar); write StatOutput to *_UI/_DB.xlsx."""
        if self._stat_checked:
            return
        if self.query_file is None:
            raise RuntimeError("Call load_query_file() first")
        self._stat_checked = True
        expected = self.source.fetch_stat_bar_table(self.query_file)
        if not expected.rows:
            self._fail("Stat bar: the StatQuery returned no rows")
            return
        exp = self._expected_stat_dict(expected)
        for spec in self.STATS:
            action_log.stat_bar_count_from_db(spec.name, exp.get(spec.name, ""))
        header = [s.name for s in self.STATS]
        ui_row = [self.stats.get(s.name, "") for s in self.STATS]
        exp_row = [str(exp.get(s.name, "")) for s in self.STATS]
        base = self.output_dir / self.query_file.name
        excel_writer.write_sheet(
            base.with_name(base.name + "_UI.xlsx"), self.STAT_UI_SHEET, header, [ui_row]
        )
        excel_writer.write_sheet(
            base.with_name(base.name + "_DB.xlsx"), self.STAT_DB_SHEET, header, [exp_row]
        )
        action_log.compare_step(self.STAT_UI_SHEET, self.STAT_DB_SHEET)
        cmp_table = compare_tables([ui_row], [exp_row], header, header)
        cmp_counts = compare_counts(self.stats, exp)
        cmp = Comparison(
            cmp_table.passed and cmp_counts.passed,
            1,
            1,
            list(dict.fromkeys(cmp_table.problems + cmp_counts.problems)),
        )
        self._record("StatBar", cmp, ui_count=1, exp_count=1)

    # ------------------------------------------------------------------ result tabs
    def open_tab(self, name: str):
        spec = self.TABS[name]
        xp = self.repo.xpath(spec.tab)
        action_log.say(f"openTab {name!r} key={spec.tab!r}")
        if self.ui.is_visible(xp):
            self.ui.click(xp, repo_key=spec.tab)
        else:
            self._open_from_more_menu(spec)
        self.ui.wait_idle()

    def _open_from_more_menu(self, spec: TabSpec):
        raise RuntimeError(f"Tab '{spec.name}' is not visible and {self.NAME} has no 'More' menu handler")

    def read_results_table(self, spec: TabSpec) -> Table:
        """Read the result table (Katalon ReadCasesTableKatalon). Per-app rules: table_reader.read_table_data."""
        return read_table_data(
            self.ui,
            app_key=self.NAME,
            table_xpath=self.repo.xpath(spec.table),
            header_xpath=self.repo.xpath(spec.header),
            next_xpath=self.repo.xpath(spec.next),
            next_repo_key=spec.next,
            **options_from_spec(
                spec,
                self.MAX_PAGES,
                pagination_max_pages=self.settings.pagination_max_pages,
                tab_row_limit=self.settings.tab_row_limit,
            ),
        )

    def _tab_enabled_for_verify(self, tabs_key: str) -> bool:
        from Commons.tab_setting import tab_is_enabled

        aliases = getattr(self, "TAB_VERIFY_ALIASES", None)
        return tab_is_enabled(self.settings.tab_execution, tabs_key, aliases)

    def verify_tab(self, name: str):
        """Katalon multiFunction: read the tab from the UI, get the expected data, compare, check stat bar."""
        spec = self.TABS[name]
        if self.query_file is None:
            raise RuntimeError("Call load_query_file() first")
        if not self._tab_enabled_for_verify(name):
            action_log.ui_action(f"Skipped {spec.name} tab (disabled in Config/tab_setting.yaml).")
            self.results.append(
                {
                    "check": spec.name,
                    "status": "SKIPPED",
                    "detail": "disabled in Config/tab_setting.yaml",
                }
            )
            return
        stat_value = self._stat_value(spec.stat)
        action_log.multifunc_stat(str(self.stats.get(spec.stat, stat_value)), stat_value)
        if stat_value == 0:
            action_log.skip_zero_stat()
            action_log.ui_action(f"Skipped {spec.name} tab (stat bar count is 0).")
            self.results.append({"check": spec.name, "status": "SKIPPED", "detail": "stat bar count is 0"})
            return
        self.open_tab(name)
        tab_count = active_result_tab_record_count(self.ui)
        if tab_count == 0:
            action_log.skip_zero_tab_count()
            action_log.ui_action(f"Skipped {spec.name} tab (result tab count is 0).")
            self.results.append(
                {"check": spec.name, "status": "SKIPPED", "detail": "result tab count is 0"}
            )
            return
        ui_table = self.read_results_table(spec)
        action_log.say(f"ReadExcel.Memgraph sheet={spec.db_sheet!r} tab={spec.input_tab!r}")
        tab_label = spec.label or spec.name
        expected = self.source.fetch_tab_table(
            self.query_file, spec.input_tab, tab_display_name=tab_label
        )
        base = self.output_dir / self.query_file.name
        excel_writer.write_sheet(base.with_name(base.name + "_UI.xlsx"), spec.ui_sheet, ui_table.header, ui_table.rows)
        excel_writer.write_sheet(base.with_name(base.name + "_DB.xlsx"), spec.db_sheet, expected.header, expected.rows)
        action_log.compare_step(spec.ui_sheet, spec.db_sheet)
        cmp = compare_tables(ui_table.rows, expected.rows, ui_table.header, expected.header)
        self._record(spec.name, cmp, ui_count=len(ui_table.rows), exp_count=len(expected.rows))
        action_log.say("Control is before validate stat bar function from multifunction")
        self.verify_statbar()

    # ------------------------------------------------------------------ static pages
    def verify_static_data(self, sheet_name: str):
        """Verify one sheet in <app>_StaticData.xlsx (Katalon verifyStaticData)."""
        from Commons.static_data import verify_static_page

        problems = verify_static_page(self, sheet_name)
        if problems:
            self._fail(f"Static data '{sheet_name}':\n  " + "\n  ".join(problems))
        else:
            self.results.append({"check": f"Static {sheet_name}", "status": "PASSED", "detail": ""})

    # ------------------------------------------------------------------ results
    def _record(self, check: str, cmp: Comparison, ui_count: int, exp_count: int):
        status = "PASSED" if cmp.passed else "FAILED"
        self.results.append(
            {"check": check, "status": status, "detail": cmp.summary(), "ui": ui_count, "db": exp_count}
        )
        if not cmp.passed:
            self.failures.append(f"[{check}] {cmp.summary()}")

    def _fail(self, message: str):
        self.failures.append(message)
        self.results.append({"check": "check", "status": "FAILED", "detail": message})

    def _failed_result_tab_labels(self) -> List[str]:
        """Human-readable tab names for result-tab checks that failed (excludes stat bar / static)."""
        labels: List[str] = []
        tabs = getattr(self, "TABS", {})
        for r in self.results:
            if r.get("status") != "FAILED":
                continue
            check = r.get("check", "")
            if check in ("StatBar", "check") or str(check).startswith("Static "):
                continue
            spec = tabs.get(check)
            label = (spec.label or spec.name) if spec else check
            if label not in labels:
                labels.append(label)
        return labels

    def assert_no_failures(self):
        """Fail the test if any tab / stat bar check failed. Called automatically at the end of a test."""
        if self.failures:
            tab_summary = self._failed_result_tab_labels()
            summary_block = "\n".join(f"Mismatch in {name} tab" for name in tab_summary)
            if summary_block:
                print(summary_block, flush=True)
            detail = (
                f"{self.NAME} {self.query_file.name if self.query_file else ''}: "
                f"{len(self.failures)} check(s) failed"
            )
            body = "\n\n".join(self.failures)
            if summary_block:
                raise AssertionError(f"{detail}\n\n{summary_block}\n\n{body}")
            raise AssertionError(f"{detail}\n\n{body}")

    def report(self) -> str:
        lines: List[str] = []
        for r in self.results:
            if "ui" in r:
                tail = f"UI={r['ui']} DB={r['db']}"
                if r["status"] == "FAILED" and r.get("detail"):
                    head = r["detail"].split("\n", 1)[0]
                    if not head.startswith("OK"):
                        tail = f"{tail}  — {head}"
            else:
                tail = r.get("detail", "")
            lines.append(f"{r['check']:<16} {r['status']:<8} {tail}")
        return "\n".join(lines)
