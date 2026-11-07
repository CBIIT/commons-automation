"""
CCDI Hub: https://ccdi.cancer.gov

Hub-specific static and functional checks. Navbar Explore opens C3DC Explore Participants —
there is no CCDI-specific Explore or result tabs.
"""
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit

from playwright.sync_api import Error as PlaywrightError, expect

from Commons import action_log, excel_writer
from Commons.base_app import BaseApp, StatSpec
from Commons.static_data import _link_href_for_env
from Commons.settings import input_dir
from Commons.apps.ccdi.publications import load_release_publications, normalize, publication_id_candidates, review_publications

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
        """Verify Home copy/links after the testcase's explicit navigation steps.

        Expected values stay in CCDI_StaticData.xlsx. Banner acceptance,
        navigation and control checks are separate, visible Excel steps.
        """
        self.verify_static_data("HomePage")

    def verify_home_controls(self):
        """Check Home inputs in a separate Excel step without submitting forms."""
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

    # --- About page verification ---

    def verify_about_page_data(self):
        """Verify About content against the shared workbook's AboutPage sheet.

        The testcase accepts the banner and navigates through the About menu.
        The shared verifier prints expected/actual text and link URLs, records
        every mismatch, and writes the AboutPage output sheet.
        """
        self.verify_static_data("AboutPage")

    # --- Publication controls and baseline review ---

    def _publication_check(self, name, check):
        """Record a publication-control result without changing other app checks."""
        try:
            detail = check() or ""
            self.results.append({"check": f"Publications {name}", "status": "PASSED", "detail": detail})
            status = "PASSED"
        except (PlaywrightError, AssertionError, ValueError, KeyError) as err:
            detail, status = str(err), "FAILED"
            self._fail(f"Publications {name}: {detail}")
        with action_log.pytest_table_output_live():
            print(f"[Publications] {name}: {status}\n  {detail.splitlines()[0] if detail else ''}", flush=True)

    def load_publications_source(self, filename):
        """Load the release tracker for review, without approving UI differences."""
        path = Path(input_dir(self.NAME)) / filename
        self._publications_source = load_release_publications(path)
        self._publications_categories = {}
        self._publications_searches = {}
        self._publications_source_path = str(path)
        with action_log.pytest_table_output_live():
            print(f"[Publications source] {len(self._publications_source['records'])} released IDs; {self._publications_source['counts']}; {len(self._publications_source['excluded'])} explicitly excluded rows", flush=True)

    def _publication_count(self):
        text = self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first.inner_text()
        return int(text.replace(",", "").strip())

    def select_publication_category(self, category):
        """Select a category using desktop tabs or the responsive dropdown."""
        assert category in ("All", "Primary", "Secondary", "Abstracts"), category
        assert urlsplit(self.page.url).path == "/publications", f"Not on /publications: {self.page.url}"
        tab = self.ui.visible(self.repo.xpath(f"Publications/{category}Tab"))
        if tab.count():
            tab.first.click()
            expect(tab.first).to_have_class(re.compile("tabListItemActive"))
        else:
            self.page.locator(".tabDropdownItem.first:visible").click()
            self.ui.visible(f"//li[normalize-space()='{category}']").first.click()
            expect(self.page.locator(".tabDropdownItem.first:visible")).to_contain_text(category)
        count = self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first
        expect(count).to_have_text(re.compile(r"^[\d,]+$"))
        if self._publication_count():
            expect(self.page.locator('nav[aria-label="pagination navigation"] button[aria-current="true"]')).to_have_text("1")

    def _read_publication_page(self):
        """Read card fields from the rendered DOM, including the real Read More href."""
        records = self.page.locator(".publicationsItem").evaluate_all("""cards => cards.map(card => {
            const text = selector => (card.querySelector(selector)?.textContent || '').trim();
            const meta = Array.from(card.querySelectorAll('.publicationsItemConference')).map(e => ({
                type:(e.querySelector('.publicationsText2')?.textContent || '').trim(),
                value:(e.querySelector('.publicationsItemConferenceLink')?.textContent || '').trim()
            }));
            const main = meta.find(m => m.type !== 'PMID') || {};
            return {id:card.id, title:text('.publicationsItemTitle'), date:text('.publicationsItemDate'),
                type:main.type || '', venue:main.value || '', pmid:meta.find(m => m.type === 'PMID')?.value || '',
                tags:Array.from(card.querySelectorAll('.publicationsItemTag')).map(e => e.textContent.trim()),
                summary:(card.querySelector('.publicationsItemContent')?.innerText || '').trim(),
                url:card.querySelector('a.readMoreButtonContainer')?.getAttribute('href') || '', category:''};
        })""")
        for record in records:
            for key in ("id", "title", "date", "type", "venue", "pmid", "summary"):
                record[key] = normalize(record[key])
            record["tags"] = sorted(normalize(v) for v in record["tags"])
            assert record["id"] and record["title"], "A publication card has no ID/title"
            assert urlsplit(record["url"]).scheme in ("http", "https"), f"Invalid Read More URL: {record['id']}"
        return records

    def _collect_publication_pages(self):
        """Traverse every result page; fail on repeated IDs, gaps or wrong page sizes."""
        total = self._publication_count()
        if total == 0:
            expect(self.page.locator(".publicationsItem")).to_have_count(0)
            return []
        self.page.locator(".publicationsItem").first.wait_for(state="visible")
        first = self._read_publication_page()
        size = len(first)
        assert 0 < size <= total, f"{size} cards for {total} results"
        pages = math.ceil(total / size)
        assert pages <= 200, f"Unexpected pagination size: {pages} pages"
        records, seen = [], set()
        for number in range(1, pages + 1):
            if number > 1:
                previous_id = self.page.locator(".publicationsItem").first.get_attribute("id")
                button = self.page.locator('nav[aria-label="pagination navigation"] button').filter(has_text=re.compile(fr"^{number}$"))
                button.click()
                expect(button).to_have_attribute("aria-current", "true")
                self.page.wait_for_function("previous => document.querySelector('.publicationsItem')?.id !== previous", arg=previous_id, timeout=10000)
            current = first if number == 1 else self._read_publication_page()
            wanted_size = size if number < pages else total - size * (pages - 1)
            assert len(current) == wanted_size, f"Page {number}: {len(current)} cards; expected {wanted_size}"
            assert self._publication_count() == total, "Result count changed while paginating"
            for record in current:
                assert record["id"] not in seen, f"Repeated publication {record['id']} on page {number}"
                seen.add(record["id"])
                records.append(record)
            with action_log.pytest_table_output_live():
                print(f"[Publications page] {number}/{pages}: {len(current)} cards", flush=True)
        assert len(records) == total, f"Collected {len(records)} cards; displayed count is {total}"
        return records

    def verify_publications_category(self, category):
        def check():
            self.select_publication_category(category)
            records = self._collect_publication_pages()
            if category != "All":
                for record in records:
                    record["category"] = category
            self._publications_categories[category] = records
            return f"{category}: {len(records)} unique cards; all pagination pages verified"
        self._publication_check(category, check)

    def verify_publications_partition(self):
        """Check that category results are disjoint and together match All."""
        def check():
            groups = self._publications_categories
            assert set(groups) == {"All", "Primary", "Secondary", "Abstracts"}, "A category was not collected"
            all_ids = {r["id"] for r in groups["All"]}
            combined = set()
            for category in ("Primary", "Secondary", "Abstracts"):
                ids = {r["id"] for r in groups[category]}
                assert not combined & ids, f"Category overlap in {category}: {combined & ids}"
                combined |= ids
            assert combined == all_ids, f"Category membership differs from All: {combined ^ all_ids}"
            return f"Primary + Secondary + Abstracts = All ({len(all_ids)} records), without duplicates"
        self._publication_check("category membership", check)

    def search_publications(self, keyword):
        """Type a keyword and explicitly click this page's Search button."""
        self.ui.visible(self.repo.xpath("Publications/SearchInput")).first.fill(keyword)
        self.submit_publications_search()

    def submit_publications_search(self):
        self.ui.visible(self.repo.xpath("Publications/SearchButton")).first.click()

    def clear_publications_search(self):
        """Clear the input; the next visible Excel step applies the empty search."""
        def check():
            self.ui.visible(self.repo.xpath("Publications/ClearSearch")).first.click()
            expect(self.ui.visible(self.repo.xpath("Publications/SearchInput")).first).to_have_value("")
            return "Search input cleared (results reset by the separate Search step)"
        self._publication_check("clear search input", check)

    def verify_publications_search(self, keyword, expected_id):
        def check():
            expect(self.ui.visible(self.repo.xpath("Publications/SearchInput")).first).to_have_value(keyword)
            assert expected_id in self._publications_source["records"], f"Expected search ID {expected_id} is not in the source workbook"
            self.page.wait_for_function("total => Number(document.querySelector('.totalNum').textContent.replaceAll(',', '')) < total", arg=len(self._publications_categories["All"]), timeout=15000)
            self.page.locator(f".publicationsItem[id='{expected_id}']").wait_for(state="visible", timeout=15000)
            records = self._collect_publication_pages()
            ids = {r["id"] for r in records}
            assert expected_id in ids, f"Search did not return expected publication {expected_id}"
            assert len(ids) < len(self._publications_categories["All"]), "Search did not narrow the publication list"
            previous = self._publications_searches.get(keyword.casefold())
            if previous is not None:
                assert previous == ids, "Case-only search change returned different publications"
            self._publications_searches[keyword.casefold()] = ids
            return f"'{keyword}': {len(ids)} results; expected publication found; case-insensitive results consistent"
        self._publication_check(f"search {keyword}", check)

    def verify_publications_reset(self):
        def check():
            expect(self.ui.visible(self.repo.xpath("Publications/SearchInput")).first).to_have_value("")
            expected = {r["id"] for r in self._publications_categories["All"]}
            expect(self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first).to_have_text(str(len(expected)), timeout=15000)
            ids = {r["id"] for r in self._read_publication_page()}
            assert ids <= expected and ids, "Reset results are not from All publications"
            return f"Empty search restores All ({len(expected)} results)"
        self._publication_check("reset results", check)

    def verify_empty_publications_search(self):
        def check():
            expect(self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first).to_have_text("0")
            expect(self.page.locator(".publicationsItem")).to_have_count(0)
            return "No-match search shows 0 results and no stale cards"
        self._publication_check("no-match search", check)

    def write_publication_results(self):
        """Save observed records and review differences; never approve a baseline."""
        groups = self._publications_categories
        observed = {r["id"]: dict(r) for r in groups.get("All", [])}
        for category in ("Primary", "Secondary", "Abstracts"):
            for record in groups.get(category, []):
                if record["id"] in observed:
                    observed[record["id"]]["category"] = category
        source = self._publications_source
        differences = review_publications(source, observed)
        review = {"status": "PENDING USER CONFIRMATION", "url": self.page.url,
            "source_path": self._publications_source_path, "source": source, "observed": observed,
            "ui_counts": {category: len(records) for category, records in groups.items()}, "differences": differences,
            "id_candidates": publication_id_candidates(source, observed)}
        (self.output_dir / "Publications_Baseline_Review.json").write_text(json.dumps(review, indent=2, ensure_ascii=False))
        headers = ["ID", "Title", "Category", "Date", "Type", "Venue", "PMID", "Tags", "Read More URL", "Visible summary"]
        for category, records in groups.items():
            excel_writer.write_sheet(self.output_dir / "Output_CCDI_Publications.xlsx", category, headers,
                [[r["id"], r["title"], category, r["date"], r["type"], r["venue"], r["pmid"], ", ".join(r["tags"]), r["url"], r["summary"]] for r in records])
        with action_log.pytest_table_output_live():
            print(f"[Publications review] {len(source['records'])} workbook IDs; {len(observed)} UI IDs; {len(differences)} review items. Expected data has NOT been updated or approved.", flush=True)

    # --- Functional Home controls (separate from static verification) ---

    # Functional helpers are opt-in Excel actions. Static page checks above do
    # not call them, and no behavior in BaseApp or other portals is changed.
    CONTROL_TIMEOUT_MS = 15000

    @staticmethod
    def _control_url_matches(actual, expected, *, document=False):
        """Compare a destination independently of the link's current href.

        Allow www canonicalization, HTTPS upgrades and query parameter ordering.
        A configured fragment must still match (HTTP requests omit fragments).
        """
        got, want = urlsplit(actual), urlsplit(expected)
        return (
            (got.scheme == want.scheme or (want.scheme == "http" and got.scheme == "https"))
            and (got.hostname or "").removeprefix("www.") == (want.hostname or "").removeprefix("www.")
            and got.port == want.port
            and (got.path.rstrip("/") or "/") == (want.path.rstrip("/") or "/")
            and sorted(parse_qsl(got.query, keep_blank_values=True)) == sorted(parse_qsl(want.query, keep_blank_values=True))
            and (document or not want.fragment or got.fragment == want.fragment)
        )

    def _control_url(self, expected):
        return urljoin(self.settings.url, _link_href_for_env(expected, self.settings.env))

    def _run_control_check(self, key, expected, check):
        """Record one functional outcome, clean up new tabs and restore Home.

        Each Excel row remains independent: one broken external site must not
        prevent the rest of the page's buttons and links from being exercised.
        """
        pages_before = set(self.page.context.pages)
        self._control_destination = self.page
        actual, detail, passed = "", "", False
        with action_log.pytest_table_output_live():
            print(f"[Controls] {key}\n  Expected: {expected}", flush=True)
        try:
            actual = check()
            passed = True
            self.results.append({"check": f"Control {key}", "status": "PASSED", "detail": actual})
        except (PlaywrightError, AssertionError, ValueError, OSError) as err:
            actual = self._control_destination.url
            detail = str(err)
            self._fail(f"Control '{key}': {detail}")
        finally:
            for popup in set(self.page.context.pages) - pages_before:
                if not popup.is_closed():
                    popup.close()
            checks = getattr(self, "_control_checks", None)
            if checks is None:
                self._control_checks = checks = []
            checks.append([key, expected, actual, "PASSED" if passed else "FAILED", detail])
            with action_log.pytest_table_output_live():
                print(f"  Actual: {actual}\n  Result: {'PASSED' if passed else 'FAILED'}" + (f"\n  Reason: {detail.splitlines()[0]}" if detail else ""), flush=True)
            if urlsplit(self.page.url).path not in ("/", "/home"):
                self.page.goto(urljoin(self.settings.url, "/home"), wait_until="domcontentloaded", timeout=self.CONTROL_TIMEOUT_MS)
                self.ui.loc(self.repo.xpath("Static/HomePage/BannerTitle")).first.wait_for(state="visible", timeout=self.CONTROL_TIMEOUT_MS)

    def verify_link_navigation(self, key, expected_url):
        """Click and verify a destination; Filter may specify 'href => landing'."""
        source, expected = self._control_destinations(expected_url)
        display = f"{source} => {expected}" if source != expected else expected
        self._run_control_check(key, display, lambda: self._click_control_link(key, expected, source=source))

    def verify_carousel_link(self, key, expected_url):
        """Center a moving resource card, then apply the same navigation check."""
        source, expected = self._control_destinations(expected_url)
        def check():
            self._center_control_carousel_link(key)
            return self._click_control_link(key, expected, source=source)
        display = f"{source} => {expected}" if source != expected else expected
        self._run_control_check(key, display, check)

    def _control_destinations(self, value):
        source, separator, landing = value.partition(" => ")
        assert source.strip(), "Expected link URL is required in Filter"
        source = self._control_url(source.strip())
        return source, self._control_url(landing.strip()) if separator else source

    def _click_control_link(self, key, expected, *, source=None):
        """Require a real click, correct URL, successful document and visible body.

        Cross-host redirects are accepted only when the browser's HTTP redirect
        chain proves they started at the configured destination. This does not
        accept an unrelated page opened by a broken JavaScript click handler.
        """
        assert urlsplit(expected).scheme in ("http", "https"), "Only web links are included; email/signup are excluded"
        source = source or expected
        assert urlsplit(source).scheme in ("http", "https"), "Email links are excluded from functional checks"
        xpath = self.repo.xpath(key)
        raw = self.ui.loc(xpath).first
        # The carousel export anchor has zero width; its visible image is the
        # actual hit target. Click that image normally so the anchor handles it.
        export_icon = raw.locator("img.exportIcon")
        is_export = export_icon.count() > 0
        el = raw if is_export else self.ui.visible(xpath).first
        click_target = export_icon.first if is_export else el
        href = urljoin(self.page.url, el.get_attribute("href") or "")
        assert self._control_url_matches(href, source), f"Link points to {href}; expected {source}"
        documents = []
        def capture(response):
            # Initial popup responses can precede frame creation in Playwright.
            # Store the document first, then associate it after the popup loads.
            if response.request.is_navigation_request() and response.request.resource_type == "document":
                documents.append(response)
        def is_destination(response, destination):
            try:
                return response.frame == destination.main_frame
            except PlaywrightError:
                return self._control_url_matches(response.url, destination.url, document=True)
        def redirected(destination):
            if source != expected:
                return False  # An explicit landing URL must match exactly.
            if urlsplit(expected).fragment and urlsplit(destination.url).fragment != urlsplit(expected).fragment:
                return False
            for response in reversed(documents):
                if not is_destination(response, destination) or not self._control_url_matches(response.url, destination.url, document=True):
                    continue
                request = response.request.redirected_from
                while request is not None:
                    if self._control_url_matches(request.url, expected, document=True):
                        return True
                    request = request.redirected_from
            return False
        self.page.context.on("response", capture)
        try:
            if el.get_attribute("target") == "_blank":
                with self.page.expect_popup(timeout=self.CONTROL_TIMEOUT_MS) as event:
                    click_target.click(timeout=self.CONTROL_TIMEOUT_MS, no_wait_after=True)
                destination = event.value
            else:
                click_target.click(timeout=self.CONTROL_TIMEOUT_MS, no_wait_after=True)
                destination = self.page
            self._control_destination = destination
            destination.wait_for_url(lambda url: self._control_url_matches(str(url), expected) or redirected(destination), timeout=self.CONTROL_TIMEOUT_MS)
            destination.wait_for_load_state("domcontentloaded", timeout=self.CONTROL_TIMEOUT_MS)
            expect(destination.locator("body")).to_be_visible(timeout=self.CONTROL_TIMEOUT_MS)
            expect(destination.locator("body")).not_to_have_text(re.compile(r"^\s*$"), timeout=self.CONTROL_TIMEOUT_MS)
            for response in documents:
                if is_destination(response, destination):
                    assert response.status < 400, f"HTTP {response.status}: {response.url}"
            title = destination.title()
            assert not re.search(r"access denied|forbidden|page not found|^404\b|just a moment", title, re.I), f"Destination shows an error/challenge page: {title}"
            assert self._control_url_matches(destination.url, expected) or redirected(destination), f"Landed at {destination.url}; expected {expected}"
            suffix = " (HTTP redirect verified)" if not self._control_url_matches(destination.url, expected) else ""
            return destination.url + suffix
        finally:
            self.page.context.remove_listener("response", capture)

    def _pause_control_carousel(self):
        toggle = self.page.locator(".pauseButton:visible").first
        if toggle.inner_text().strip().upper() == "PAUSE":
            toggle.click()
            expect(toggle).not_to_have_text("PAUSE", timeout=3000)
        self._wait_control_carousel()

    def _wait_control_carousel(self):
        self.page.wait_for_function("() => !document.querySelector('#carouselList').getAnimations({subtree:true}).some(a => a.playState === 'running')", timeout=5000)

    def _move_control_carousel(self, selector):
        before = self.page.locator("#carouselList a.listItemContent").first.get_attribute("href")
        self.page.locator(selector).click(timeout=self.CONTROL_TIMEOUT_MS)
        self.page.wait_for_function("before => document.querySelector('#carouselList a.listItemContent').getAttribute('href') !== before", arg=before, timeout=5000)
        self._wait_control_carousel()

    def _center_control_carousel_link(self, key):
        """Use the real arrow control until the target reaches the active frame."""
        self._pause_control_carousel()
        target = self.ui.loc(self.repo.xpath(key)).first
        for _ in range(13):
            centered = target.evaluate("e => { const a=document.querySelector('.activeFrame').getBoundingClientRect(), b=e.closest('.carousel__item').getBoundingClientRect(); return Math.abs((a.top+a.bottom-b.top-b.bottom)/2)<35; }")
            if centered:
                target.locator("xpath=..").hover(timeout=self.CONTROL_TIMEOUT_MS)
                return
            self._move_control_carousel(".downButton")
        raise AssertionError(f"Carousel never centered {key}")

    def verify_home_control_action(self, key, value=""):
        """Exercise a non-link Home control and verify its observable effect."""
        name = key.rsplit("/", 1)[-1]
        def check():
            if name in ("ResourcesMenu", "AboutMenu"):
                button = self.ui.loc(self.repo.xpath(key)).first
                button.click()
                item = self.page.get_by_role("link", name=value, exact=True).first
                expect(item).to_be_visible(timeout=self.CONTROL_TIMEOUT_MS)
                button.click()
                expect(item).not_to_be_visible(timeout=5000)
                return f"Menu opens and closes; '{value}' becomes visible"
            if name in ("SearchButton", "SearchEnter"):
                assert value, "Search keyword is required in Filter"
                self.page.locator("#search_desktop").fill(value)
                if name == "SearchEnter":
                    self.page.locator("#search_desktop").press("Enter")
                else:
                    self.ui.loc(self.repo.xpath(key)).first.click()
                expected = self._control_url('/sitesearch?' + urlencode({'keyword': value}))
                self.page.wait_for_url(lambda url: self._control_url_matches(str(url), expected), timeout=self.CONTROL_TIMEOUT_MS)
                expect(self.page.get_by_role("heading", name="Search Results", exact=True)).to_be_visible()
                expect(self.page.locator("#global_search_input")).to_have_value(value)
                panel = self.page.get_by_role("tabpanel")
                expect(panel.get_by_role("progressbar")).to_have_count(0, timeout=self.CONTROL_TIMEOUT_MS)
                expect(panel).to_contain_text(re.compile(r"[1-9][\d,]*\s*results", re.I), timeout=self.CONTROL_TIMEOUT_MS)
                return self.page.url + " (search results loaded)"
            if name in ("CarouselPrevious", "CarouselNext"):
                self._pause_control_carousel()
                self._move_control_carousel(".upButton" if name == "CarouselPrevious" else ".downButton")
                return "Carousel displays a different resource"
            if name == "CarouselPause":
                self._pause_control_carousel()
                before = self.page.locator("#carouselList a.listItemContent").first.get_attribute("href")
                # Sample beyond the autoplay interval: PAUSE must stop movement,
                # not merely change the toggle's text.
                self.page.wait_for_timeout(3500)
                assert self.page.locator("#carouselList a.listItemContent").first.get_attribute("href") == before, "Paused carousel kept moving"
                self.page.locator(".pauseButton:visible").first.click()
                self.page.wait_for_function("before => document.querySelector('#carouselList a.listItemContent').getAttribute('href') !== before", arg=before, timeout=7000)
                return "Pause stops autoplay; Start resumes it"
            if name == "BackToTop":
                self.page.locator("footer:visible").first.scroll_into_view_if_needed()
                assert self.page.evaluate("window.scrollY") > 100, "Page did not scroll to the footer"
                self.ui.loc(self.repo.xpath(key)).first.click(timeout=self.CONTROL_TIMEOUT_MS)
                self.page.wait_for_function("window.scrollY <= 5", timeout=5000)
                return "Back to Top returns the page to the top"
            raise ValueError(f"Unsupported Home control: {name}")
        self._run_control_check(key, value or name, check)

    def write_home_control_results(self):
        """Write per-control evidence separately from static-data output files."""
        excel_writer.write_sheet(
            self.output_dir / "Output_TC01_CCDI_Verify_HomePage_Controls.xlsx", "Controls",
            ["Control", "Expected", "Actual", "Result", "Detail"], getattr(self, "_control_checks", []),
        )

    # --- Navigation ---

    def open_explore(self):
        """Explore menu → C3DC Explore Participants (not a CCDI explore URL)."""
        self.click(
            "Navbar/Explore_Menu",
            ui_message="C3DC Explore Participants opened from CCDI Explore.",
        )
