"""Static and functional Home page checks for the CCDI Hub.

HomePageControls supplies the existing Excel actions to the CCDI app adapter.
Static content and functional controls remain separate Excel actions.
"""
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit

from playwright.sync_api import Error as PlaywrightError, expect

from Commons import action_log, excel_writer
from Commons.static_data import _link_href_for_env


class HomePageControls:
    """Home content, input, link and carousel checks using the CCDI app context."""

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

    # --- Functional Home controls ---

    # These opt-in Excel actions use the app's page, settings and result storage.
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
