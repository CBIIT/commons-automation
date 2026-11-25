"""Verify page-size choices, page ranges, navigation boundaries, and complete table data."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from playwright.sync_api import expect

from Commons.table_navigation import NavigationOptions, TableNavigation


# ---------------------------------------------------------------------------
# App overrides: controls, independent totals, identities, and resize behavior
# ---------------------------------------------------------------------------

@dataclass
class PaginationOptions(NavigationOptions):
    page_size_key: str = ''
    range_key: str = ''
    footer_selector: str = '[class*="MuiTablePagination-root"]'
    identity_columns: tuple[str, ...] = ()
    total_reader: Callable | None = None
    size_change_policy: str = 'first'  # first, keep_first_row, or same_page
    preserve_order: bool = True


def parse_page_range(text):
    match = re.search(r'([\d,]+)\s*(?:[-–—]|\bto\b)\s*([\d,]+)\s*(?:of|/)\s*([\d,]+)', text)
    assert match, f'Unrecognized pagination range: {text!r}'
    start, end, total = (int(value.replace(',', '')) for value in match.groups())
    valid = (start, end) == (0, 0) if total == 0 else 1 <= start <= end <= total
    assert valid, f'Invalid pagination range: {text!r}'
    return start, end, total


def resized_offset(offset, old_size, new_size, total, policy):
    if not total or policy == 'first':
        return 0
    if policy == 'keep_first_row':
        return offset // new_size * new_size
    assert policy == 'same_page', f'Unknown page-size change policy: {policy}'
    return min(offset // old_size, (total - 1) // new_size) * new_size


class TablePagination(TableNavigation):
    def __init__(self, app, tab, options=None):
        super().__init__(app, tab, options or PaginationOptions())
        self.evidence = {'tab': tab, 'sizes': []}

    # -----------------------------------------------------------------------
    # Scoped native/MUI dropdowns and range labels (including duplicate toolbars)
    # -----------------------------------------------------------------------

    def footer(self):
        footers = self.root.locator(self.options.footer_selector + ':visible')
        return footers.first if footers.count() else self.root

    def size_control(self):
        if self.options.page_size_key:
            return self.app.ui.visible(self.app.repo.xpath(self.options.page_size_key)).first
        controls = self.footer().locator('select:visible, [role="combobox"]:visible, '
                                         '[class*="MuiSelect-root"][role="button"]:visible')
        assert controls.count() == 1, 'Configure page_size_key when the table has no unique page-size control'
        return controls.first

    def current_size(self):
        control = self.size_control()
        value = control.input_value() if control.evaluate("el=>el.tagName==='SELECT'") else control.inner_text()
        assert re.fullmatch(r'\s*\d+\s*', value), f'Unsupported selected page size: {value!r}'
        return int(value)

    def status(self):
        text = (self.app.ui.visible(self.app.repo.xpath(self.options.range_key)).first.inner_text()
                if self.options.range_key else self.footer().inner_text())
        return parse_page_range(text)

    @staticmethod
    def option_size(option):
        value = option.get_attribute('data-value') or option.get_attribute('value') or option.inner_text().strip()
        return int(value) if re.fullmatch(r'\d+', value) and int(value) > 0 else None

    def menu(self):
        menu = self.app.page.locator('[role="listbox"]:visible').last
        expect(menu).to_be_visible(timeout=self.app.ui.timeout_ms)
        return menu

    def available_sizes(self):
        control = self.size_control()
        native = control.evaluate("el=>el.tagName==='SELECT'")
        if native:
            options = control.locator('option').all()
        else:
            control.click()
            options = self.menu().get_by_role('option').all()
        sizes = []
        for option in options:
            value = self.option_size(option)
            if value is not None and option.is_enabled():
                sizes.append(value)
        if not native:
            self.app.page.keyboard.press('Escape')
            expect(self.app.page.locator('[role="listbox"]:visible')).to_have_count(0)
        assert sizes and len(set(sizes)) == len(sizes), f'Invalid page-size choices: {sizes}'
        return sizes

    def select_size(self, size):
        control = self.size_control()
        if control.evaluate("el=>el.tagName==='SELECT'"):
            option = next((option for option in control.locator('option').all()
                           if self.option_size(option) == size and option.is_enabled()), None)
            assert option is not None, f'Page size {size} is unavailable'
            control.select_option(option.get_attribute('value') or str(size))
        else:
            control.click()
            option = next((option for option in self.menu().get_by_role('option').all()
                           if self.option_size(option) == size and option.is_enabled()), None)
            assert option is not None, f'Page size {size} is unavailable'
            option.click()
        self.wait_until(lambda: self.current_size() == size, f'Page-size selection did not update to {size}')

    # -----------------------------------------------------------------------
    # Every page: range, row count, exact records, and enabled/disabled buttons
    # -----------------------------------------------------------------------

    def button_disabled(self, direction):
        button = self.page_button(direction)
        assert button is not None, f'Table {direction} page control was not found'
        return button.is_disabled() or button.get_attribute('aria-disabled') == 'true'

    def capture(self, offset, size, total, baseline=None):
        start, end = (offset + 1, min(offset + size, total)) if total else (0, 0)
        expected_count = end - offset
        def ready():
            return (self.current_size() == size and self.status() == (start, end, total)
                    and len(self.snapshot()) == expected_count)
        self.wait_until(ready, f'Page did not settle at {start}-{end} of {total} with size {size}')
        rows = self.snapshot()
        assert self.button_disabled('previous') == (offset == 0), f'Incorrect Previous state at {start}-{end}'
        assert self.button_disabled('next') == (end == total), f'Incorrect Next state at {start}-{end}'
        if baseline is not None:
            wanted = baseline[offset:end]
            assert Counter(map(tuple, rows)) == Counter(map(tuple, wanted)), f'Wrong records on page {start}-{end}'
            if self.options.preserve_order:
                assert rows == wanted, f'Pagination changed record order at {start}-{end}'
        return rows, {'start': start, 'end': end, 'total': total, 'row_count': len(rows),
                      'previous_disabled': offset == 0, 'next_disabled': end == total}

    def forward(self, size, total, baseline=None):
        rows, pages = [], []
        for index in range(self.options.max_pages):
            offset = index * size
            page, detail = self.capture(offset, size, total, baseline)
            rows.extend(page)
            pages.append(detail)
            if detail['end'] == total:
                assert len(rows) == total, 'Pagination did not collect the advertised total'
                if self.options.identity_columns:
                    indices = [self.header_names.index(name) for name in self.options.identity_columns]
                    ids = [tuple(row[index] for index in indices) for row in rows]
                    assert all(all(part for part in identity) for identity in ids), 'Pagination has empty identities'
                    assert len(ids) == len(set(ids)), 'Pagination repeated record identities'
                return rows, pages
            self.move_page(self.page_button('next'))
        raise AssertionError('Pagination exceeds max_pages; narrow the filters or raise the limit')

    def backward(self, size, total, baseline, page_count):
        pages = []
        for index in range(page_count - 2, -1, -1):
            self.move_page(self.page_button('previous'))
            _, detail = self.capture(index * size, size, total, baseline)
            pages.append(detail)
        assert self.button_disabled('previous'), 'Previous must be disabled after returning to page one'
        return pages

    # -----------------------------------------------------------------------
    # Full page-size verification, mid-page resizing, restoration, and evidence
    # -----------------------------------------------------------------------

    def verify(self, report_name, page_sizes=None):
        folder = self.app.output_dir / 'result_tabs' / Path(report_name).stem
        folder.mkdir(parents=True, exist_ok=True)
        try:
            self.app.open_tab(self.tab)
            expect(self.headers().first).to_be_visible(timeout=self.app.ui.timeout_ms)
            self.header_names = [' '.join(header.inner_text().split()) for header in self.headers().all()]
            initial = {}
            def loaded():
                try:
                    size = self.current_size()
                    start, end, count = self.status()
                    reference = self.options.total_reader() if self.options.total_reader else count
                    if reference is None or reference != count:
                        return False
                    if len(self.snapshot()) != (end - start + 1 if count else 0):
                        return False
                    initial.update(size=size, total=count)
                    return True
                except AssertionError:
                    return False
            self.wait_until(loaded, 'Pagination controls, rows, and result total did not finish loading')
            original_size, total = initial['size'], initial['total']
            assert total <= self.options.max_rows, 'Too many pagination rows; narrow the filters or raise max_rows'
            if self.options.total_reader:
                assert self.options.total_reader() == total, 'Pagination total differs from the result-tab count'
            available = self.available_sizes()
            sizes = available if page_sizes is None else list(page_sizes)
            self.evidence.update(available_sizes=available, requested_sizes=sizes,
                                 record_count=total, original_size=original_size)
            assert sizes and all(type(size) is int and size > 0 for size in sizes), 'Page sizes must be positive integers'
            assert len(sizes) == len(set(sizes)), 'Page sizes must not repeat'
            assert set(sizes) <= set(available), f'Required page sizes unavailable: {sorted(set(sizes)-set(available))}; available: {available}'
            self.rewind()
            baseline, baseline_pages = self.forward(original_size, total)
            self.evidence['baseline_pages'] = baseline_pages
            self.backward(original_size, total, baseline, len(baseline_pages))
            for index, size in enumerate(sizes):
                self.select_size(size)
                _, pages = self.forward(size, total, baseline)
                result = {'page_size': size, 'forward_pages': pages,
                          'backward_pages': self.backward(size, total, baseline, len(pages))}
                self.evidence['sizes'].append(result)
                if total > size and len(sizes) > 1:
                    self.move_page(self.page_button('next'))
                    self.capture(size, size, total, baseline)
                    new_size = sizes[(index + 1) % len(sizes)]
                    self.select_size(new_size)
                    offset = resized_offset(size, size, new_size, total, self.options.size_change_policy)
                    _, detail = self.capture(offset, new_size, total, baseline)
                    result['mid_page_resize'] = {'from_size': size, 'to_size': new_size, **detail}
                    self.rewind()
                else:
                    result['mid_page_resize'] = {'status': 'NOT_APPLICABLE',
                                                'reason': 'Only one page or one available size'}
            self.select_size(original_size)
            self.capture(0, original_size, total, baseline)
            self.evidence['restored'] = True
            self.app.results.append({'check': f'{self.tab} pagination', 'status': 'PASSED',
                                     'detail': f'{total} records retained at page sizes {sizes}; ranges and both navigation directions verified'})
            return self.evidence
        except Exception as exc:
            self.evidence['error'] = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            (folder / f'{self.tab.lower()}_pagination.json').write_text(json.dumps(self.evidence, indent=2))
