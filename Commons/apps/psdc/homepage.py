"""Reusable functional checks for PSDC Home links and controls."""
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import Error as PlaywrightError, expect

from Commons import action_log, excel_writer


class HomePageControls:
    CONTROL_TIMEOUT_MS = 15000

    def _home_control_locator(self, key):
        """Reject ambiguous locators instead of silently clicking a mobile copy."""
        locator = self.page.locator(self.repo.xpath(key))
        expect(locator).to_have_count(1)
        expect(locator).to_be_visible()
        expect(locator).to_be_enabled()
        return locator

    def _restore_home(self):
        """Restore Home after same-tab navigation; close popups separately."""
        if urlsplit(self.page.url).fragment not in ('', '/'):
            self.page.goto(urljoin(self.settings.url, '/#/'), wait_until='domcontentloaded')
        banner = self.page.locator(self.repo.xpath('Home/WarningBan_Continue_Btn'))
        if banner.is_visible():
            self.accept_banner()
        expect(self.page.locator("#tile1_title")).to_be_visible(timeout=self.CONTROL_TIMEOUT_MS)

    def _run_home_control(self, key, expected, check):
        """Keep per-control evidence and continue checking after an individual failure."""
        before = set(self.page.context.pages)
        actual, detail, passed = '', '', False
        try:
            actual = check()
            passed = True
            self.results.append({'check': f'Control {key}', 'status': 'PASSED', 'detail': actual})
        except (PlaywrightError, AssertionError, ValueError) as error:
            detail = str(error)
            self._fail(f"Home control '{key}': {detail}")
        finally:
            for popup in set(self.page.context.pages) - before:
                if not popup.is_closed():
                    popup.close()
            if not hasattr(self, '_home_control_results'):
                self._home_control_results = []
            self._home_control_results.append([key, expected, actual, 'PASSED' if passed else 'FAILED', detail])
            with action_log.pytest_table_output_live():
                print(f"[Home Controls] {key}: {'PASSED' if passed else 'FAILED'}\n  Expected: {expected}\n  Actual: {actual}" + (f'\n  Reason: {detail}' if detail else ''), flush=True)
            self._restore_home()

    def verify_home_link(self, key, expected_url):
        """Exercise internal routes and external browser handoffs against Excel URLs.

        External checks verify a real browser navigation request, not third-party
        page content or availability. Email/phone hrefs are checked without
        launching operating-system applications.
        """
        def check():
            assert expected_url, 'Expected destination is required in Filter'
            element = self._home_control_locator(key)
            expected = urljoin(self.settings.url, expected_url)
            href = urljoin(self.settings.url, element.get_attribute('href') or '')
            assert href == expected, f'Link points to {href}; expected {expected}'
            scheme = urlsplit(expected).scheme
            if scheme in ('mailto', 'tel'):
                return f'{href} (protocol href verified; external application not launched)'
            assert scheme in ('http', 'https'), f'Unsupported link scheme: {scheme}'
            if urlsplit(expected).netloc == urlsplit(self.settings.url).netloc:
                element.click(timeout=self.CONTROL_TIMEOUT_MS)
                # The logo uses / rather than /#/. Both identify PSDC Home.
                self.page.wait_for_url(lambda u: str(u) == expected, timeout=self.CONTROL_TIMEOUT_MS)
                if urlsplit(expected).fragment not in ('', '/'):
                    expect(self.page.locator('#tile1_title')).to_be_hidden(timeout=self.CONTROL_TIMEOUT_MS)
                else:
                    banner = self.page.locator(self.repo.xpath('Home/WarningBan_Continue_Btn'))
                    if banner.is_visible():
                        self.accept_banner()
                    expect(self.page.locator('#tile1_title')).to_be_visible(timeout=self.CONTROL_TIMEOUT_MS)
                expect(self.page.locator('body')).not_to_have_text('', timeout=self.CONTROL_TIMEOUT_MS)
                return self.page.url
            # Capture the first document request from the actual click. This
            # remains deterministic when a social site redirects to login.
            with self.page.context.expect_event(
                'request', predicate=lambda r: r.is_navigation_request() and r.resource_type == 'document' and r.url.rstrip('/') == expected.split('#', 1)[0].rstrip('/'),
                timeout=self.CONTROL_TIMEOUT_MS,
            ) as navigation:
                if element.get_attribute('target') == '_blank':
                    with self.page.expect_popup(timeout=self.CONTROL_TIMEOUT_MS):
                        element.click(timeout=self.CONTROL_TIMEOUT_MS, no_wait_after=True)
                else:
                    element.click(timeout=self.CONTROL_TIMEOUT_MS, no_wait_after=True)
            return f'{navigation.value.url} (browser navigation requested)'
        self._run_home_control(key, expected_url, check)

    def verify_home_control(self, key, value=''):
        """Check About menu visibility and Back to Top scrolling behavior."""
        def check():
            if key == 'NavBar/About-Tab':
                button = self._home_control_locator(key)
                links = [self.page.locator(self.repo.xpath(f'NavBar/{name}')) for name in (
                    'AboutPage-Link', 'AccessData-Link', 'AnalyzeData-Link', 'GraphQL-Link', 'Support-Link')]
                button.click()
                for link in links:
                    expect(link).to_be_visible()
                button.click()
                for link in links:
                    expect(link).to_be_hidden()
                return 'About menu opens and closes; all menu links become visible'
            if key == 'HomeControls/BackToTop':
                self.page.locator(self.repo.xpath('Static/HomePage/HelpDeskLink')).scroll_into_view_if_needed()
                assert self.page.evaluate('window.scrollY') > 100, 'Page did not scroll down'
                self._home_control_locator(key).click()
                self.page.wait_for_function('window.scrollY <= 5', timeout=5000)
                return 'Back to Top returns the page to the top'
            raise ValueError(f'Unknown Home control: {key}')
        self._run_home_control(key, value or key, check)

    def write_home_control_results(self):
        excel_writer.write_sheet(
            self.output_dir / 'Output_TC01_PSDC_Verify_HomePage_Controls.xlsx', 'Controls',
            ['Control', 'Expected', 'Actual', 'Result', 'Detail'], getattr(self, '_home_control_results', []),
        )
