"""Shared table snapshots, page navigation, and readiness for result-table checks."""
from dataclasses import dataclass
import time

from Commons.table_reader import pagination_prev_xpath


@dataclass
class NavigationOptions:
    link_columns: tuple[str, ...] = ()
    settle_ms: int = 200
    max_rows: int = 500
    max_pages: int = 100


class TableNavigation:
    def __init__(self, app, tab, options=None):
        self.app, self.tab = app, tab
        self.options = options or NavigationOptions()
        self.spec = app.TABS[tab]
        self.xpath = app.repo.xpath(self.spec.table)
        self.root = app.ui.visible(self.xpath).first
        self.header_names = []

    # -----------------------------------------------------------------------
    # Table headers and complete cell snapshots
    # -----------------------------------------------------------------------

    def headers(self):
        return self.root.locator('thead tr').last.locator(':scope > th, :scope > [role="columnheader"]')

    def snapshot(self):
        count = self.headers().count()
        return self.root.locator('tbody > tr').evaluate_all('''(rows, {count, links}) => rows
          .filter(row => row.getBoundingClientRect().height && row.cells.length === count
                         && !row.querySelector('td[colspan]'))
          .map(row => Array.from(row.cells).map((cell, index) => {
            const text = links.includes(index) ? cell.querySelector('a[href]')?.href || cell.innerText : cell.innerText;
            return (text || '').split(/\\n+/).map(line => line.replace(/\\s+/g, ' ').trim()).filter(Boolean).join('; ');
          }))''', {'count': count, 'links': [index for index, name in enumerate(self.header_names)
                                           if name in self.options.link_columns]})

    # -----------------------------------------------------------------------
    # Scoped Next/Previous controls and complete dataset traversal
    # -----------------------------------------------------------------------

    def page_button(self, direction):
        fallback = self.app.repo.xpath(self.spec.next)
        label = 'Next page' if direction == 'next' else 'Previous page'
        button = self.root.locator(', '.join(
            f'button[{attribute}="{value}"]:visible'
            for attribute in ('aria-label', 'title') for value in (label, label.lower())))
        if not button.count():
            xpath = fallback if direction == 'next' else pagination_prev_xpath('', fallback)
            button = self.app.ui.visible(xpath)
        return button.first if button.count() else None

    def move_page(self, button):
        before = self.snapshot()
        button.click()
        self.wait_until(lambda: self.snapshot() and self.snapshot() != before, 'Pagination did not replace table rows')

    def rewind(self):
        for _ in range(self.options.max_pages):
            previous = self.page_button('previous')
            if previous is None or previous.is_disabled() or previous.get_attribute('aria-disabled') == 'true':
                return
            self.move_page(previous)
        raise AssertionError('Pagination rewind exceeded the configured page limit')

    def read_all(self):
        self.rewind()
        rows, signatures = [], set()
        for _ in range(self.options.max_pages):
            page = self.snapshot()
            assert page, 'The table has no readable data rows'
            signature = tuple(tuple(row) for row in page)
            assert signature not in signatures, 'Pagination repeated a page'
            signatures.add(signature)
            rows.extend(page)
            assert len(rows) <= self.options.max_rows, 'Too many table rows; narrow the filters or raise max_rows'
            next_button = self.page_button('next')
            if next_button is None or next_button.is_disabled() or next_button.get_attribute('aria-disabled') == 'true':
                self.rewind()
                return rows
            self.move_page(next_button)
        raise AssertionError('Verification requires all pages; narrow the filters or raise max_pages')

    # -----------------------------------------------------------------------
    # Poll data changes and DOM stability without long fixed waits
    # -----------------------------------------------------------------------

    def wait_until(self, predicate, message):
        deadline = time.monotonic() + self.app.ui.timeout_ms / 1000
        while time.monotonic() < deadline:
            if predicate():
                return
            self.app.page.wait_for_timeout(50)
        raise AssertionError(message)

    def wait_for_stable_rows(self):
        previous, changed = self.snapshot(), time.monotonic()
        def stable():
            nonlocal previous, changed
            current = self.snapshot()
            if current != previous:
                previous, changed = current, time.monotonic()
            return bool(current) and (time.monotonic() - changed) * 1000 >= self.options.settle_ms
        self.wait_until(stable, 'Table rows did not settle')

