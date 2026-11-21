"""Shared file-cart mechanics; portal adapters own navigation and export behavior.

Cart tables are read by their displayed headers. Explore's table_reader intentionally
applies result-tab column rules and row limits, so it is not used for cart snapshots.
"""
from __future__ import annotations

import csv
from collections import Counter
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from playwright.sync_api import expect

from Commons import action_log


@dataclass(frozen=True)
class FileRecord:
    """Independent metadata captured before adding a file to the cart."""
    values: tuple[tuple[str, str], ...]
    identity_fields: tuple[str, ...] = ('name',)

    @property
    def name(self) -> str:
        return dict(self.values)['name']

    @property
    def identity(self) -> str:
        fields = dict(self.values)
        parts = [fields[key] for key in self.identity_fields]
        return parts[0] if len(parts) == 1 else json.dumps(parts, separators=(',', ':'))


def normalize_value(field: str, value: str) -> str:
    if field == 'name':
        return value.strip()
    if field in ('participants', 'samples'):
        return ';'.join(sorted(set(v.strip() for v in re.split(r'[,;\n]', value) if v.strip())))
    return ' '.join(value.split())


def records_from_cells(headers, rows, columns: Mapping[str, str], identity_fields=('name',), *, require_unique=True) -> tuple[FileRecord, ...]:
    """Resolve column positions from headers; fail on schema drift or ambiguous names."""
    normalized = [normalize_value('', h).casefold() for h in headers]
    positions = {}
    for field, label in columns.items():
        assert normalized.count(label.casefold()) == 1, f'Expected one {label!r} column, found {headers}'
        positions[field] = normalized.index(label.casefold())
    records = []
    for row in rows:
        # Empty-state rows have a single colspan cell, not a file-name data cell.
        if len(row) != len(headers):
            assert len(row) == 1, f'Unexpected cart row width: {row}'
            continue
        record = FileRecord(tuple((field, normalize_value(field, row[index])) for field, index in positions.items()), tuple(identity_fields))
        assert record.name, 'File row has an empty name'
        records.append(record)
    if require_unique:
        assert len({r.identity for r in records}) == len(records), 'File identities are ambiguous; expose the portal file-ID column before comparing this data'
    return tuple(records)


def compare_records(expected, actual) -> dict:
    """Compare membership and mapped metadata, without depending on row order."""
    wanted = {r.identity: dict(r.values) for r in expected}
    got = {r.identity: dict(r.values) for r in actual}
    assert len(wanted) == len(expected), 'Expected file baseline contains duplicate identities'
    assert len(got) == len(actual), 'Cart contains duplicate file identities'
    changed = {name: {'expected': wanted[name], 'actual': got[name]}
               for name in wanted.keys() & got.keys() if any(got[name].get(field) != value for field, value in wanted[name].items())}
    return {'missing': sorted(wanted.keys() - got.keys()), 'unexpected': sorted(got.keys() - wanted.keys()), 'changed': changed}


def file_size_bytes(value: str) -> float:
    match = re.fullmatch(r'([\d,.]+)\s*(B|KB|MB|GB|TB)', value.strip(), re.I)
    assert match, f'Unsupported displayed file size: {value!r}'
    return float(match[1].replace(',', '')) * 1024 ** ('B', 'KB', 'MB', 'GB', 'TB').index(match[2].upper())


class FileCartApp:
    """Opt-in composition; unrelated BaseApp subclasses do not acquire cart behavior."""
    FILE_CART_CLASS = None

    @property
    def file_cart(self):
        if '_file_cart' not in self.__dict__:
            if self.FILE_CART_CLASS is None:
                raise NotImplementedError('This portal has no file-cart adapter')
            self._file_cart = self.FILE_CART_CLASS(self)
        return self._file_cart


class FileCart:
    """Shared selection, snapshots, sorting, pagination and artifact handling."""
    identity_fields = ('name',)
    source_columns: Mapping[str, str] = {'name': 'File Name'}
    cart_columns: Mapping[str, str] = {'name': 'File Name'}

    def __init__(self, app):
        self.app = app
        self.selected: dict[str, FileRecord] = {}
        self.expected: dict[str, FileRecord] = {}
        self.manifest_path: Path | None = None

    def control(self, name, scope=None):
        root = scope or self.app.page
        return root.locator('xpath=' + self.app.repo.xpath('FileCart/' + name))

    def visible(self, name):
        locator = self.app.ui.visible(self.app.repo.xpath('FileCart/' + name))
        # Bento repeats source controls above and below tables and retains hidden
        # tab toolbars. Select the top visible copy only for these known repeats.
        repeated = ('Navigation', 'Next', 'Previous', 'SourceNext', 'SourcePrevious',
                    'PageStatus', 'PageSize', 'AddSelected', 'AddAll')
        return locator.first if name in repeated else locator

    def open_source(self):
        raise NotImplementedError('The portal adapter must open its file source')

    def open(self):
        self.visible('Navigation').click()
        expect(self.control('Table')).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.wait_for_total(len(self.expected))

    def wait_for_total(self, total):
        expect(self.visible('PageStatus')).to_contain_text(re.compile(rf'\bof\s+{total:,}\s*$', re.I), timeout=self.app.ui.timeout_ms)

    def read_page(self, source=False):
        table = self.visible('SourceTable' if source else 'Table')
        cells = table.evaluate("""t => ({headers:[...t.querySelectorAll('thead th')].map(c=>c.innerText.trim()),
            rows:[...t.querySelectorAll('tbody tr')].map(r=>[...r.children].map(c=>c.innerText.trim()))})""")
        return records_from_cells(cells['headers'], cells['rows'], self.source_columns if source else self.cart_columns, self.identity_fields, require_unique=not source)

    def move_page(self, direction, source=False):
        """Wait for the file names to change, not for an arbitrary delay."""
        before = self.read_page(source)
        assert before, 'Cannot paginate an empty file table'
        control = self.visible(('Source' if source else '') + direction)
        expect(control).to_be_enabled()
        control.click()
        # Loading rows can briefly replace the old tbody. Require actual new file
        # names, not merely different/empty tbody text, before recording a page.
        columns = self.source_columns if source else self.cart_columns
        fields = [{'name': key, 'label': columns[key]} for key in self.identity_fields]
        self.app.page.wait_for_function(r"""({xpath, previous, fields}) => {
          const nodes = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
          const norm=(key,value)=> {
            if(['participants','samples'].includes(key)) return [...new Set(value.split(/[,;\n]/).map(x=>x.trim()).filter(Boolean))].sort().join(';');
            return key==='name' ? value.trim() : value.trim().replace(/\s+/g,' ');
          };
          for (let i=0; i<nodes.snapshotLength; i++) {
            const t=nodes.snapshotItem(i); if(!t.getBoundingClientRect().width) continue;
            const headers=[...t.querySelectorAll('thead th')].map(x=>x.innerText.trim().toLowerCase());
            const row=t.querySelector('tbody tr'); if(!row) continue;
            const cells=fields.map(f=>row.cells[headers.indexOf(f.label.toLowerCase())]);
            if(cells.some(c=>!c)) continue;
            const identity=cells.map((c,n)=>norm(fields[n].name,c.innerText));
            if(JSON.stringify(identity)!==JSON.stringify(previous)) return true;
          }
          return false;
        }""", arg={'xpath': self.app.repo.xpath('FileCart/' + ('SourceTable' if source else 'Table')),
                   'previous': [dict(before[0].values)[key] for key in self.identity_fields], 'fields': fields},
            timeout=self.app.ui.timeout_ms)

    def select_files(self, count=3):
        """Select a caller-sized sample on this source page; zero means the full page."""
        assert count >= 0, 'File selection count must be nonnegative'
        table = self.visible('SourceTable')
        expect(table.locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)
        rows = self.read_page(source=True)
        chosen = rows if count == 0 else rows[:count]
        assert chosen and (count == 0 or len(chosen) == count), f'Not enough source files for selection: requested {count}, found {len(rows)}'
        assert len({r.identity for r in chosen}) == len(chosen), 'Selected source rows have ambiguous file identities; choose distinct files'
        assert not set(self.selected) & {r.identity for r in chosen}, 'Source selection repeated file names; wait for a distinct page or clear the selection'
        if count == 0:
            # The header checkbox selects this page in one action. Keep the
            # independently captured metadata for the same exact row set.
            header = table.locator('thead input[type=checkbox]')
            expect(header).to_be_enabled()
            header.check()
            expect(table.locator('tbody input[type=checkbox]:checked')).to_have_count(len(chosen))
        else:
            for index in range(len(chosen)):
                checkbox = table.locator('tbody tr').nth(index).locator('input[type=checkbox]')
                expect(checkbox).to_be_enabled()
                checkbox.check()
        self.selected.update((record.identity, record) for record in chosen)
        action_log.ui_action(f'Selected {len(chosen)} source files; retained {len(self.selected)} unique IDs.')

    def add_selected(self):
        assert self.selected, 'Select files before adding them'
        button = self.visible('AddSelected')
        expect(button).to_be_enabled()
        button.click()
        self.expected.update(self.selected)
        self.app.ui.wait_idle()

    def snapshot(self, source=False):
        previous = self.visible('SourcePrevious' if source else 'Previous')
        while previous.is_enabled():
            self.move_page('Previous', source)
        records, seen = [], set()
        for _ in range(self.app.MAX_PAGES):
            rows = self.read_page(source)
            names = {r.identity for r in rows}
            assert not names & seen, 'Cart pagination repeated file names'
            records.extend(rows)
            seen.update(names)
            if self.visible('SourceNext' if source else 'Next').is_disabled():
                return tuple(records)
            self.move_page('Next', source)
        raise AssertionError('Cart pagination exceeded the configured page guard')

    def verify(self, report_name):
        self.wait_for_total(len(self.expected))
        actual = self.snapshot()
        difference = compare_records(tuple(self.expected.values()), actual)
        folder = self.app.output_dir / Path(report_name).stem
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'cart_comparison.json').write_text(json.dumps({
            'expected': [dict(r.values) for r in self.expected.values()],
            'actual': [dict(r.values) for r in actual], 'difference': difference}, indent=2))
        assert not any(difference.values()), f'Cart content mismatch: {difference}'
        self.verify_badge(len(actual))
        self.app.results.append({'check': 'File cart membership', 'status': 'PASSED', 'detail': f'{len(actual)} exact files and mapped metadata verified'})
        return actual

    def verify_badge(self, total):
        expect(self.visible('Badge')).to_have_text(str(total), timeout=self.app.ui.timeout_ms)

    def verify_persistence(self, report_name):
        self.open_source()
        self.open()
        self.verify(report_name)
        self.app.page.reload(wait_until='domcontentloaded')
        self.verify(report_name)

    def set_page_size(self, count):
        assert count > 0, 'Page size must be positive'
        self.visible('PageSize').click()
        self.app.page.get_by_role('option', name=str(count), exact=True).click()
        self.wait_for_total(len(self.expected))
        expect(self.visible('PageSize')).to_have_text(str(count))
        while self.visible('Previous').is_enabled():
            self.move_page('Previous')
        if self.expected:
            expect(self.visible('Table').locator('tbody tr')).to_have_count(min(count, len(self.expected)), timeout=self.app.ui.timeout_ms)

    def verify_sort(self, field, direction):
        assert direction in ('asc', 'desc'), 'Sort direction must be asc or desc'
        label = self.cart_columns[field]
        header = self.visible('Table').get_by_role('columnheader', name=label, exact=True)
        header.get_by_role('button').click()
        if header.get_attribute('direction') != direction:
            header.get_by_role('button').click()
        expect(header).to_have_attribute('direction', direction)
        self.app.ui.wait_idle()
        rows = self.snapshot()
        difference = compare_records(tuple(self.expected.values()), rows)
        assert not any(difference.values()), f'Sorting changed cart membership: {difference}'
        values = [dict(r.values)[field] for r in rows]
        key = file_size_bytes if field == 'size' else str.casefold
        assert values == sorted(values, key=key, reverse=direction == 'desc'), f'Cart {label} is not sorted {direction}: {values}'
        self.app.results.append({'check': f'Cart sort {label} {direction}', 'status': 'PASSED', 'detail': f'{len(rows)} files retained'})

    def save_download(self, trigger, report_name):
        folder = self.app.output_dir / Path(report_name).stem
        folder.mkdir(parents=True, exist_ok=True)
        with self.app.page.expect_download(timeout=self.app.ui.timeout_ms) as event:
            trigger()
        download = event.value
        assert download.failure() is None, f'Cart download failed: {download.failure()}'
        path = folder / Path(download.suggested_filename).name
        download.save_as(path)
        assert path.stat().st_size, 'Downloaded cart manifest is empty'
        self.manifest_path = path
        return path

    def download_manifest(self, report_name):
        raise NotImplementedError('The portal adapter must define its export interaction')

    def verify_manifest(self):
        raise NotImplementedError('The portal adapter must define its manifest schema')

    def remove_one(self):
        raise NotImplementedError('The portal adapter must define removal behavior')

    def remove_all(self, confirm):
        raise NotImplementedError('The portal adapter must define confirmation behavior')


def verify_csv_manifest(path, expected, *, name_column, participant_column=None, required_columns=()):
    """Validate an adapter's CSV schema and exact file/participant membership."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames and set((name_column, *required_columns)) <= set(reader.fieldnames), f'Unexpected manifest headers: {reader.fieldnames}'
        rows = list(reader)
    assert all(row[name_column] for row in rows), 'Manifest contains an empty file name'
    if participant_column:
        assert participant_column in reader.fieldnames, f'Missing manifest column {participant_column}'
    wanted = Counter((record.name, dict(record.values)['participants'] if participant_column else '')
                     for record in expected)
    actual = Counter((row[name_column], normalize_value('participants', row[participant_column]) if participant_column else '')
                     for row in rows)
    assert actual == wanted, f'Manifest membership differs: missing={dict(wanted-actual)}, unexpected={dict(actual-wanted)}'
    if 'drs_uri' in required_columns:
        uris = [row['drs_uri'] for row in rows]
        assert len(uris) == len(set(uris)), 'Manifest repeats the same DRS file identity'
    return rows
