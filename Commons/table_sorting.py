"""Discover result-table sort controls and verify complete ascending/descending results."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Mapping

from playwright.sync_api import expect

from Commons import action_log
from Commons.table_navigation import TableNavigation


# ---------------------------------------------------------------------------
# Comparison rules: applications override data semantics, never the sort loop
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SortRule:
    kind: str = 'text'
    separator: str | None = None
    casefold: bool = False
    missing: tuple[str, ...] = ('',)
    unknown_number: Decimal | None = None

    def key(self, text, direction):
        values = list(text) if isinstance(text, (list, tuple)) else (text.split(self.separator) if self.separator else [text])
        keys = []
        for value in values:
            value = ' '.join(value.split())
            if value in self.missing:
                if value and self.unknown_number is not None:
                    keys.append(self.unknown_number)
                continue
            if self.kind == 'number':
                try:
                    number = Decimal(value.replace(',', ''))
                    assert number.is_finite(), f'Non-finite sort value: {value!r}'
                    keys.append(number)
                except InvalidOperation as exc:
                    raise AssertionError(f'Invalid numeric sort value: {value!r}') from exc
            else:
                keys.append(value.casefold() if self.casefold else value)
        if not keys:
            return None
        return min(keys) if direction == 'asc' else max(keys)


@dataclass
class SortingOptions:
    rules: Mapping[str, SortRule] = field(default_factory=dict)
    identity_column: str = ''
    response_matches: Callable | None = None  # (response, column_name, direction) -> bool
    response_ids: Callable | None = None  # Completed response -> displayed page identities
    link_columns: tuple[str, ...] = ()  # Compare link destinations instead of repeated link labels.
    cell_values: Callable | None = None  # (column, identity, displayed_text) -> complete scalar/list value.
    settle_ms: int = 200  # Quiet period for DOM-only adapters; server adapters use response readiness.
    max_rows: int = 500
    max_pages: int = 100


def infer_rule(name, values):
    """Infer scalar numeric columns while retaining identifier columns as text."""
    if re.search(r'\b(id|identifier|accession)\b', name, re.IGNORECASE):
        return SortRule()
    present = [value for value in values if value not in ('', 'Not Reported')]
    if present:
        try:
            if all(Decimal(value.replace(',', '')).is_finite() for value in present):
                return SortRule(kind='number', missing=('', 'Not Reported'))
        except InvalidOperation:
            pass
    return SortRule()


def assert_sorted(values, direction):
    """Compare numeric/text keys with missing values last in both directions."""
    present = [value for value in values if value is not None]
    wanted = sorted(present, reverse=direction == 'desc') + [None] * (len(values) - len(present))
    assert values == wanted, f'Values are not sorted {direction}: {values}'


# ---------------------------------------------------------------------------
# DOM discovery: native ARIA headers and Material UI sort labels
# ---------------------------------------------------------------------------

SORT_CONTROL = '[class*="MuiTableSortLabel-root"], button[data-sort], [role="button"][data-sort]'


class TableSorting(TableNavigation):
    def __init__(self, app, tab, options=None):
        super().__init__(app, tab, options or SortingOptions())
        self.columns = []
        self.orders = {}
        self.evidence = {'tab': tab, 'columns': [], 'skipped': []}

    def discover(self):
        expect(self.headers().first).to_be_visible(timeout=self.app.ui.timeout_ms)
        for index, header in enumerate(self.headers().all()):
            name = ' '.join(header.inner_text().split())
            self.header_names.append(name)
            controls = header.locator(SORT_CONTROL)
            if controls.count() and controls.first.is_visible() and controls.first.is_enabled():
                self.columns.append((index, name))
            elif not controls.count() and header.get_attribute('aria-sort') is not None:
                self.columns.append((index, name))
            else:
                self.evidence['skipped'].append({'column': name or f'Column {index + 1}',
                                                  'reason': 'No enabled sort control'})
        assert self.columns, 'No supported sortable headers found in the active table'
        assert len({name for _, name in self.columns}) == len(self.columns), 'Sortable header names must be unique'

    def control(self, index):
        header = self.headers().nth(index)
        controls = header.locator(SORT_CONTROL)
        return controls.first if controls.count() else header

    def direction(self, index):
        header = self.headers().nth(index)
        aria = header.get_attribute('aria-sort')
        if aria in ('ascending', 'descending'):
            return 'asc' if aria == 'ascending' else 'desc'
        control = self.control(index)
        active = 'TableSortLabel-active' in (control.get_attribute('class') or '')
        if active:
            if control.locator('[class*="iconDirectionAsc"]').count():
                return 'asc'
            if control.locator('[class*="iconDirectionDesc"]').count():
                return 'desc'
            return header.get_attribute('direction')
        return None

    # -----------------------------------------------------------------------
    # Sort clicks and readiness: adapters can wait for their exact data response
    # -----------------------------------------------------------------------

    def wait_for_ids(self, name, ids):
        labels = [' '.join(h.inner_text().split()) for h in self.headers().all()]
        identity = labels.index(self.options.identity_column)
        self.wait_until(lambda: [row[identity] for row in self.snapshot()] == ids,
                        f'{name}: table rows did not match the completed sort response')

    def key(self, index, name, row, direction):
        value = row[index]
        if self.options.cell_values:
            identity = row[self.header_names.index(self.options.identity_column)]
            value = self.options.cell_values(name, identity, value)
        return self.rules[name].key(value, direction)

    def click(self, index, name):
        if self.options.response_matches:
            next_direction = 'desc' if self.direction(index) == 'asc' else 'asc'
            cached_ids = self.orders.get((name, next_direction))
            if cached_ids is not None:
                # Client-side caches can restore a previously observed order without HTTP.
                self.control(index).click()
                self.wait_for_ids(name, cached_ids)
                return
            with self.app.page.expect_response(lambda response: self.options.response_matches(response, name, next_direction),
                                               timeout=self.app.ui.timeout_ms) as pending:
                self.control(index).click()
            response = pending.value
            assert response.ok, f'Sort response failed: HTTP {response.status}'
            if self.options.response_ids:
                ids = self.options.response_ids(response)
                self.orders[(name, next_direction)] = ids
                self.wait_for_ids(name, ids)
        else:
            previous = self.direction(index)
            self.control(index).click()
            self.wait_until(lambda: self.direction(index) is not None and self.direction(index) != previous,
                            f'{name}: sort indicator did not change')
            self.wait_for_stable_rows()
            direction = self.direction(index)
            rule = self.rules[name]
            def ordered():
                try:
                    rows = self.snapshot()
                    assert_sorted([self.key(index, name, row, direction) for row in rows], direction)
                    return bool(rows)
                except AssertionError:
                    return False
            self.wait_until(ordered, f'{name}: sorted rows did not settle')

    def set_direction(self, index, name, direction):
        for _ in range(3):
            if self.direction(index) == direction:
                return
            self.click(index, name)
            self.wait_until(lambda: self.direction(index) is not None, f'{name}: no active sort indicator')
        raise AssertionError(f'{name}: could not select {direction} sorting')

    # -----------------------------------------------------------------------
    # Complete-table verification and saved evidence for every discovered column
    # -----------------------------------------------------------------------

    def verify(self, report_name):
        folder = self.app.output_dir / 'result_tabs' / Path(report_name).stem
        folder.mkdir(parents=True, exist_ok=True)
        try:
            self.app.open_tab(self.tab)
            self.discover()
            self.wait_until(lambda: bool(self.snapshot()), 'Sorting table did not load')
            self.wait_for_stable_rows()
            baseline = self.read_all()
            assert len(baseline) >= 2, 'Sorting needs at least two filtered records'
            self.rules = {name: self.options.rules.get(name) or infer_rule(name, [row[index] for row in baseline])
                          for index, name in self.columns}
            if self.options.response_ids:
                labels = [' '.join(h.inner_text().split()) for h in self.headers().all()]
                identity = labels.index(self.options.identity_column)
                first_page_ids = [row[identity] for row in self.snapshot()]
                for index, name in self.columns:
                    direction = self.direction(index)
                    if direction:
                        self.orders[(name, direction)] = first_page_ids
            membership = Counter(tuple(row) for row in baseline)
            self.evidence['record_count'] = len(baseline)
            failures = []
            for index, name in self.columns:
                rule = self.rules[name]
                for direction in ('asc', 'desc'):
                    action_log.say(f'Checking {self.tab}: {name} {direction}')
                    try:
                        self.set_direction(index, name, direction)
                    except AssertionError as exc:
                        self.evidence['columns'].append({'column': name, 'direction': direction,
                                                         'status': 'FAILED', 'detail': str(exc)})
                        failures.append(f'{name} {direction}: {exc}')
                        continue
                    if not self.options.response_matches:
                        def ordered():
                            try:
                                assert_sorted([self.key(index, name, row, direction) for row in self.snapshot()], direction)
                                return bool(self.snapshot())
                            except AssertionError:
                                return False
                        self.wait_until(ordered, f'{name}: sorted rows did not settle')
                    rows = self.read_all()
                    actual_membership = Counter(tuple(row) for row in rows)
                    assert actual_membership == membership, (
                        f'{name}: sorting changed table data/membership; '
                        f'missing={list((membership - actual_membership).elements())[:2]}, '
                        f'unexpected={list((actual_membership - membership).elements())[:2]}')
                    values = [self.key(index, name, row, direction) for row in rows]
                    entry = {'column': name, 'direction': direction, 'values': [str(v) if v is not None else None for v in values]}
                    try:
                        assert_sorted(values, direction)
                        entry['status'] = 'PASSED' if len(set(values)) > 1 else 'INCONCLUSIVE'
                        if entry['status'] == 'INCONCLUSIVE':
                            entry['reason'] = 'Only one distinct sort value; direction and row retention checked'
                    except AssertionError as exc:
                        entry.update(status='FAILED', detail=str(exc))
                        failures.append(f'{name} {direction}: {exc}')
                    self.evidence['columns'].append(entry)
            assert not failures, '\n'.join(failures)
            verified = sum(entry['status'] == 'PASSED' for entry in self.evidence['columns'])
            assert verified, 'No column had enough distinct values to verify sorting'
            self.app.results.append({'check': f'{self.tab} sorting', 'status': 'PASSED',
                                     'detail': f'{len(self.columns)} sortable columns, both directions, {len(baseline)} rows; {verified} meaningful order checks'})
            return self.evidence
        except Exception as exc:
            self.evidence['error'] = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            (folder / f'{self.tab.lower()}_sorting.json').write_text(json.dumps(self.evidence, indent=2))
