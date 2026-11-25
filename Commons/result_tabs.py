"""Reusable result-tab downloads; app adapters own controls and export schemas."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from playwright.sync_api import expect

from Commons.db_source import Table


# ---------------------------------------------------------------------------
# Export specifications and file parsing
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResultTabExportSpec:
    table_key: str
    download_key: str
    format_keys: Mapping[str, str]
    headers: tuple[str, ...]
    identity_columns: tuple[str, ...]
    query_tab: str
    count_query_tab: str
    filename_pattern: str


def read_csv_export(path: Path) -> Table:
    """Read quoted CSV as text, preserving identifiers and duplicate records."""
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    assert rows and rows[0], 'CSV export has no header'
    headers = rows[0]
    assert len(headers) == len(set(headers)), f'Duplicate CSV headers: {headers}'
    data = [row for row in rows[1:] if row]
    assert all(len(row) == len(headers) for row in data), 'CSV export has malformed row widths'
    return Table(headers, data)


def read_json_records(path: Path) -> list[dict]:
    """Read a JSON record array without accepting duplicate keys or non-JSON numbers."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f'Duplicate JSON key: {key}'
            result[key] = value
        return result

    def invalid_constant(value):
        raise AssertionError(f'Invalid JSON number: {value}')

    with path.open(encoding='utf-8-sig') as stream:
        records = json.load(stream, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    assert isinstance(records, list), 'JSON export must contain an array of records'
    assert all(isinstance(record, dict) for record in records), 'JSON export records must be objects'
    return records


def category_text_matches(text, categories, separator=', '):
    """Compare an unordered flattened list without splitting commas inside labels."""
    @lru_cache(None)
    def consume(remaining_text, remaining_values):
        if not remaining_values:
            return remaining_text == ''
        for index, value in enumerate(remaining_values):
            suffix = separator if len(remaining_values) > 1 else ''
            prefix = value + suffix
            if remaining_text.startswith(prefix) and consume(
                    remaining_text[len(prefix):], remaining_values[:index] + remaining_values[index + 1:]):
                return True
        return False
    return consume(text.strip(), tuple(sorted(categories)))



def compare_export(expected: Table, actual: Table, identity_columns: tuple[str, ...]) -> dict:
    """Require the same schema and exact records, independently of row order."""
    assert actual.header == expected.header, f'Export headers differ: {actual.header} != {expected.header}'
    positions = [actual.header.index(column) for column in identity_columns]
    assert positions, 'Configure at least one export identity column'
    def normalized(rows):
        assert all(len(row) == len(actual.header) for row in rows), 'Export comparison has malformed rows'
        return [tuple(str(value).strip() for value in row) for row in rows]
    wanted, got = normalized(expected.rows), normalized(actual.rows)
    for label, rows in [('Expected data', wanted), ('Export', got)]:
        identities = [tuple(row[index] for index in positions) for row in rows]
        assert all(all(part for part in key) for key in identities), f'{label} has empty identities'
        assert len(identities) == len(set(identities)), f'{label} has duplicate identities'
    missing, unexpected = Counter(wanted) - Counter(got), Counter(got) - Counter(wanted)
    return {'missing': list(missing.elements()), 'unexpected': list(unexpected.elements())}


# ---------------------------------------------------------------------------
# App integration: one result-tab helper per app instance
# ---------------------------------------------------------------------------

class ResultTabsApp:
    RESULT_TABS_CLASS = None

    @property
    def result_tabs(self):
        if '_result_tabs' not in self.__dict__:
            if self.RESULT_TABS_CLASS is None:
                raise NotImplementedError('This app has no result-tab adapter')
            self._result_tabs = self.RESULT_TABS_CLASS(self)
        return self._result_tabs


class ResultTabs:
    EXPORTS: Mapping[str, ResultTabExportSpec] = {}

    def __init__(self, app):
        self.app = app
        self.downloads: dict[tuple[str, str], Path] = {}

    # -----------------------------------------------------------------------
    # Navigation and download capture
    # -----------------------------------------------------------------------

    def export_spec(self, tab, fmt='CSV'):
        """Adapters may provide a different schema or query for another format."""
        return self.EXPORTS[tab]

    def open_tab(self, tab):
        if tab not in self.EXPORTS:
            raise ValueError(f'No export specification for {tab!r}')
        self.app.open_tab(tab)
        spec = self.EXPORTS[tab]
        expect(self.app.ui.visible(self.app.repo.xpath(spec.table_key))).to_be_visible()

    def download_trigger(self, tab, fmt):
        """App adapters return the control that actually starts the download."""
        raise NotImplementedError

    def download(self, tab, fmt, report_name):
        fmt = fmt.upper()
        spec = self.export_spec(tab, fmt)
        if fmt not in spec.format_keys:
            raise ValueError(f'{tab} does not support a configured {fmt} export')
        self.open_tab(tab)
        trigger = self.download_trigger(tab, fmt)
        expect(trigger).to_be_enabled()
        folder = self.app.output_dir / 'result_tabs' / Path(report_name).stem
        folder.mkdir(parents=True, exist_ok=True)
        with self.app.page.expect_download(timeout=self.app.ui.timeout_ms) as event:
            trigger.click()
        download = event.value
        assert download.failure() is None, f'Download failed: {download.failure()}'
        name = Path(download.suggested_filename).name
        assert re.fullmatch(spec.filename_pattern, name), f'Unexpected export filename: {name}'
        path = folder / name
        download.save_as(path)
        assert path.stat().st_size, 'Result-tab download is empty'
        self.downloads[(tab, fmt)] = path
        self.app.results.append({'check': f'{tab} {fmt} download', 'status': 'PASSED', 'detail': name})
        return path

    # -----------------------------------------------------------------------
    # Independent expected data and full-export verification
    # -----------------------------------------------------------------------

    def expected_table(self, tab, fmt='CSV'):
        spec = self.export_spec(tab, fmt)
        assert self.app.query_file is not None, 'Load the expected-data workbook first'
        source = self.app.source
        expected = source.fetch_tab_table(self.app.query_file, spec.query_tab,
                                         tab_display_name=f'{tab} export', apply_row_limit=False)
        count = source.fetch_tab_table(self.app.query_file, spec.count_query_tab,
                                      tab_display_name=f'{tab} export count', apply_row_limit=False)
        assert len(count.rows) == 1 and len(count.rows[0]) == 1, 'Expected one independent export count'
        total = int(count.rows[0][0])
        assert total > 0, 'Choose filters with at least one result for this download test'
        assert len(expected.rows) == total, f'Expected-data query is incomplete: {len(expected.rows)} of {total}'
        assert tuple(expected.header) == spec.headers, f'Expected-data schema differs from {tab} specification'
        return expected

    def prepare_comparison(self, tab, expected, actual, fmt='CSV'):
        return expected, actual

    def read_export(self, tab, fmt, path):
        if fmt == 'CSV':
            return read_csv_export(path)
        raise NotImplementedError(f'The app adapter must define its {fmt} record structure')

    def verify_download(self, tab, fmt):
        fmt = fmt.upper()
        path = self.downloads[(tab, fmt)]
        expected = self.expected_table(tab, fmt)
        actual = self.read_export(tab, fmt, path)
        expected, actual = self.prepare_comparison(tab, expected, actual, fmt)
        spec = self.export_spec(tab, fmt)
        difference = compare_export(expected, actual, spec.identity_columns)
        report = {'headers': actual.header, 'expected_count': len(expected.rows),
                  'actual_count': len(actual.rows), 'difference': difference}
        (path.parent / f'{tab.lower()}_{fmt.lower()}_comparison.json').write_text(json.dumps(report, indent=2))
        assert not any(difference.values()), f'{tab} {fmt} content mismatch: {difference}'
        self.app.results.append({'check': f'{tab} {fmt} contents', 'status': 'PASSED',
                                 'detail': f'All {len(actual.rows)} records and {len(actual.header)} columns matched independent expected data'})
        return actual


class DirectCSVResultTabs(ResultTabs):
    """Portals with one CSV button instead of a format menu."""

    def export_spec(self, tab, fmt='CSV'):
        if fmt != 'CSV':
            raise ValueError(f'{tab} supports CSV only; no {fmt} control is configured')
        return super().export_spec(tab, fmt)

    def download_trigger(self, tab, fmt):
        return self.app.ui.visible(self.app.repo.xpath(self.export_spec(tab, fmt).download_key)).first
