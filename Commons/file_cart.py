"""Shared file-cart mechanics; app adapters configure or override portal behavior.

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
from urllib.parse import urlparse

from playwright.sync_api import expect

from Commons import action_log


# ----------------------------------------------------------------------------
# File metadata: identity, normalization, comparison, and size conversion
# ----------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------
# App integration: create one cart adapter per app instance
# ----------------------------------------------------------------------------
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
    """Shared cart mechanics configured or overridden by app-specific adapters."""
    # Opt in when counts or sort indicators render before the table rows.
    wait_for_page_rows = False
    wait_for_sorted_rows = False
    clears_source_selection = False
    manifest_name = 'name'
    manifest_participants = None
    manifest_required = ()
    add_all_message = None
    empty_message = ''
    removal_message = ''
    removal_confirm = 'Yes'
    removal_cancel = 'No'

    identity_fields = ('name',)
    source_columns: Mapping[str, str] = {'name': 'File Name'}
    cart_columns: Mapping[str, str] = {'name': 'File Name'}

    # ----------------------------------------------------------------------------
    # Cart state and locator helpers
    # ----------------------------------------------------------------------------
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

    # ----------------------------------------------------------------------------
    # Navigation: open the source table or file cart
    # ----------------------------------------------------------------------------
    def open_source(self):
        raise NotImplementedError('The portal adapter must open its file source')

    def open(self):
        self.visible('Navigation').click()
        expect(self.control('Table')).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.wait_for_total(len(self.expected))

    # ----------------------------------------------------------------------------
    # Table reading and pagination: wait for data and move between pages
    # ----------------------------------------------------------------------------
    def wait_for_total(self, total):
        expect(self.visible('PageStatus')).to_contain_text(re.compile(rf'\bof\s+{total:,}\s*$', re.I), timeout=self.app.ui.timeout_ms)

    def read_page(self, source=False):
        if self.wait_for_page_rows and not source:
            status = self.visible('PageStatus').inner_text()
            match = re.search(r'([\d,]+)\s*[-–]\s*([\d,]+)\s+of\s+([\d,]+)', status, re.I)
            assert match, f'Unrecognized cart pagination: {status}'
            start, end, total = (int(value.replace(',', '')) for value in match.groups())
            if total:
                expect(self.visible('Table').locator('tbody tr')).to_have_count(end - start + 1, timeout=self.app.ui.timeout_ms)
            else:
                expect(self.visible('Empty')).to_be_visible(timeout=self.app.ui.timeout_ms)
        table = self.visible('SourceTable' if source else 'Table')
        cells = table.evaluate("""t => ({headers:[...t.querySelectorAll('thead tr:last-child > *')].map(c=>c.innerText.trim()),
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
            const headers=[...t.querySelectorAll('thead tr:last-child > *')].map(x=>x.innerText.trim().toLowerCase());
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

    # ----------------------------------------------------------------------------
    # Source selection: capture file metadata and add selected files
    # ----------------------------------------------------------------------------
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

    # ----------------------------------------------------------------------------
    # Cart verification: compare all pages, badge counts, and persistence
    # ----------------------------------------------------------------------------
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

    # ----------------------------------------------------------------------------
    # Table controls: page size, sorting, and sort verification
    # ----------------------------------------------------------------------------
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

    def set_sort(self, field, direction):
        """Set direction, optionally waiting for asynchronously rendered rows."""
        table = self.visible('Table')
        label = self.cart_columns[field]
        header = table.get_by_role('columnheader', name=label, exact=True)
        button = header.get_by_role('button')
        was_active = self.wait_for_sorted_rows and button.locator('svg').count() > 0
        previous = header.get_attribute('direction')
        button.click()
        if self.wait_for_sorted_rows and was_active:
            expect(header).to_have_attribute('direction', 'desc' if previous == 'asc' else 'asc')
        elif self.wait_for_sorted_rows:
            expect(button.locator('svg')).to_be_visible()
        if header.get_attribute('direction') != direction:
            button.click()
        expect(header).to_have_attribute('direction', direction)
        if not self.wait_for_sorted_rows:
            return
        # Some tables update the indicator before replacing tbody. The expected source
        # values provide a real readiness condition without a fixed sleep.
        key = file_size_bytes if field == 'size' else str.casefold
        values = sorted((dict(record.values)[field] for record in self.expected.values()),
                        key=key, reverse=direction == 'desc')
        headers = table.locator('thead tr').last.locator(':scope > *').all_inner_texts()
        index = [' '.join(text.split()).casefold() for text in headers].index(label.casefold())
        page_size = int(self.visible('PageSize').inner_text())
        expect(table.locator(f'tbody tr > :nth-child({index + 1})')).to_have_text(values[:page_size], timeout=self.app.ui.timeout_ms)

    def verify_sort(self, field, direction):
        assert direction in ('asc', 'desc'), 'Sort direction must be asc or desc'
        label = self.cart_columns[field]
        self.set_sort(field, direction)
        self.app.ui.wait_idle()
        rows = self.snapshot()
        difference = compare_records(tuple(self.expected.values()), rows)
        assert not any(difference.values()), f'Sorting changed cart membership: {difference}'
        values = [dict(r.values)[field] for r in rows]
        key = file_size_bytes if field == 'size' else str.casefold
        assert values == sorted(values, key=key, reverse=direction == 'desc'), f'Cart {label} is not sorted {direction}: {values}'
        self.app.results.append({'check': f'Cart sort {label} {direction}', 'status': 'PASSED', 'detail': f'{len(rows)} files retained'})

    # ----------------------------------------------------------------------------
    # Manifest downloads: save artifacts and verify their contents
    # ----------------------------------------------------------------------------
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
        self.visible('Export').click()
        return self.save_download(lambda: self.visible('Manifest').click(), report_name)

    def verify_manifest(self):
        assert self.manifest_path, 'Download a cart manifest first'
        baseline = getattr(self, 'export_records', tuple(self.expected.values()))
        rows = verify_csv_manifest(self.manifest_path, baseline, name_column=self.manifest_name,
                                  participant_column=self.manifest_participants,
                                  required_columns=self.manifest_required)
        self.app.results.append({'check': 'Cart manifest', 'status': 'PASSED',
                                 'detail': f'{len(rows)} exact files and configured participant sets verified'})

    # ----------------------------------------------------------------------------
    # Removal: delete one file or confirm/cancel removal of all files
    # ----------------------------------------------------------------------------
    def remove_one(self):
        """Remove the first visible file and retain all other expected metadata."""
        while self.visible('Previous').is_enabled():
            self.move_page('Previous')
        record = self.read_page()[0]
        self.control('RowRemove', self.visible('Table').locator('tbody tr').first).click()
        del self.expected[record.identity]
        self.wait_for_total(len(self.expected))

    def remove_all(self, confirm):
        count = len(self.expected)
        assert count, 'Add files before checking cart removal'
        self.visible('RemoveAll').click()
        dialog = self.visible('RemovalDialog')
        expect(dialog).to_be_visible(timeout=self.app.ui.timeout_ms)
        # ICDC paints overflowing text inside a zero-height paragraph. The dialog
        # must be visible, while its message is read without a visibility filter.
        expect(self.control('RemovalMessage')).to_have_text(self.removal_message.format(count=count), timeout=self.app.ui.timeout_ms)
        dialog.get_by_role('button', name=re.compile('^' + re.escape(self.removal_confirm if confirm else self.removal_cancel) + '$', re.I)).click()
        expect(dialog).not_to_be_visible()
        if confirm:
            self.expected.clear()
        self.wait_for_total(len(self.expected))

    # ----------------------------------------------------------------------------
    # Duplicate protection: re-add existing files and verify cart membership
    # ----------------------------------------------------------------------------
    def verify_duplicate_addition(self):
        """Add the original source selection twice; cart membership must stay fixed."""
        original = dict(self.selected)
        assert original and original.keys() <= self.expected.keys()
        # Wait for the original add to commit before selecting those IDs again.
        # CTDC/ICDC clear source selections asynchronously after resolving metadata.
        self.verify_badge(len(self.expected))
        checked = self.visible('SourceTable').locator('tbody input[type=checkbox]:checked')
        if self.clears_source_selection:
            expect(checked).to_have_count(0, timeout=self.app.ui.timeout_ms)
        else:
            for checkbox in checked.all():
                checkbox.uncheck()
        self.selected.clear()
        self.select_files(len(original))
        assert self.selected.keys() == original.keys(), 'Source files changed before duplicate addition'
        self.app.ui.wait_idle()
        if self.visible('AddSelected').is_disabled():
            self.app.results.append({'check': 'Duplicate cart addition', 'status': 'PASSED',
                                     'detail': 'The portal prevents resubmitting files already in the cart'})
            return
        self.add_selected()

    # ----------------------------------------------------------------------------
    # Empty state: verify the message and disabled pagination controls
    # ----------------------------------------------------------------------------
    def verify_empty(self, report_name):
        assert not self.expected
        self.verify(report_name)
        expect(self.visible('Empty')).to_have_text(self.empty_message)
        expect(self.visible('Next')).to_be_disabled()
        expect(self.visible('Previous')).to_be_disabled()

    # ----------------------------------------------------------------------------
    # Static content and help: verify cart text and the user guide
    # ----------------------------------------------------------------------------
    def verify_static(self):
        self.app.verify_static_data('FileCartPage')

    def verify_guide(self):
        """Check the README's workbook-owned content, then return to the cart."""
        self.visible('Guide').click()
        self.app.verify_static_data('FileCartGuide')
        self.visible('GuideClose').click()
        expect(self.visible('GuideDialog')).not_to_be_visible()
        self.wait_for_total(len(self.expected))

    # ----------------------------------------------------------------------------
    # External export: verify the CGC destination
    # ----------------------------------------------------------------------------
    def verify_cgc_entry(self, expected_host):
        """Check the unauthenticated destination without signing in or submitting data."""
        assert expected_host, 'Supply the expected CGC login hostname in Params'
        self.visible('Export').click()
        with self.app.page.expect_popup(timeout=self.app.ui.timeout_ms) as event:
            self.visible('CGC').click()
        popup = event.value
        try:
            popup.wait_for_url(re.compile(r'^https://' + re.escape(expected_host) + r'/'), wait_until='commit', timeout=self.app.ui.timeout_ms)
            assert urlparse(popup.url).hostname == expected_host
        finally:
            popup.close()
        self.app.results.append({'check': 'CGC export entry', 'status': 'PASSED',
                                 'detail': 'Expected login destination opened; no authentication or project submission'})

    # ----------------------------------------------------------------------------
    # Selected-file export: export a subset while preserving the full cart
    # ----------------------------------------------------------------------------
    def select_export_files(self, count):
        """Select a subset in the cart and export only those rows."""
        rows = self.read_page()
        assert 0 < count < len(rows), 'Selected-file export needs a proper subset of the current page'
        table = self.visible('Table')
        for index in range(count):
            table.locator('tbody tr').nth(index).locator('input[type=checkbox]').check()
        self.visible('SelectedScope').check()
        self.export_records = rows[:count]

    def verify_selected_export(self, report_name, count):
        self.select_export_files(count)
        self.download_manifest(report_name)
        self.verify_manifest()
        # Exporting a subset must not remove the unselected files from the cart.
        self.verify(report_name)

    # ----------------------------------------------------------------------------
    # Bulk addition: capture a bounded filtered set and add all its files
    # ----------------------------------------------------------------------------
    def add_all_filtered(self, max_files=25):
        """Allow Add All only after a caller has selected a bounded source filter."""
        text = self.visible('PageStatus').inner_text()
        total = int(re.search(r'of\s+([\d,]+)', text, re.I)[1].replace(',', ''))
        assert 0 < total <= max_files, f'Filter to 1–{max_files} files before Add All; found {total}'
        records = self.snapshot(source=True)
        assert len(records) == total
        assert len({record.identity for record in records}) == total, 'Filtered source identities are ambiguous'
        self.visible('AddAll').click()
        if self.add_all_message:
            dialog = self.visible('AddAllDialog')
            expect(dialog).to_be_visible(timeout=self.app.ui.timeout_ms)
            expect(self.control('AddAllMessage')).to_have_text(self.add_all_message.format(count=total), timeout=self.app.ui.timeout_ms)
            dialog.get_by_role('button', name=re.compile('^Yes$', re.I)).click()
            expect(dialog).not_to_be_visible()
        self.expected.update((record.identity, record) for record in records)
        self.app.ui.wait_idle()


# ----------------------------------------------------------------------------
# CSV validation: check schema, file membership, and participant mappings
# ----------------------------------------------------------------------------
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
