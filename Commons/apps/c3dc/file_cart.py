"""C3DC cart controls and CSV schema; generic file mechanics live in Commons.file_cart."""
import re

from playwright.sync_api import expect

from Commons.file_cart import FileCart, verify_csv_manifest, normalize_value


class C3DCFileCart(FileCart):
    identity_fields = ('name', 'study')
    source_columns = {'name': 'File Name', 'study': 'Study ID', 'participants': 'Participant ID',
                      'samples': 'Sample ID', 'type': 'File Type'}
    cart_columns = {**source_columns, 'size': 'File Size'}

    def open_source(self):
        self.app.open_explore_files()
        self.selected.clear()
        expect(self.visible('SourceTable').locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)

    def prepare_small_filter(self, max_files=25):
        """Choose a bounded study from the live catalog, never an assumed accession."""
        assert max_files > 0
        self.app.open_studies_listing()
        table = self.app.ui.visible(self.app.repo.xpath('StudiesPage/Table'))
        expect(table.locator('tbody tr').first).to_be_visible(timeout=self.app.ui.timeout_ms)
        cells = table.evaluate("""t=>({headers:[...t.querySelectorAll('thead th')].map(e=>e.innerText.trim()),
          rows:[...t.querySelectorAll('tbody tr')].map(r=>[...r.children].map(c=>c.innerText.trim()))})""")
        headers = [normalize_value('', h) for h in cells['headers']]
        study_col, files_col = headers.index('Study ID'), headers.index('Files Count')
        candidates = [(row[study_col], int(row[files_col].replace(',', ''))) for row in cells['rows']
                      if row[files_col].replace(',', '').isdigit() and 0 < int(row[files_col].replace(',', '')) <= max_files]
        assert candidates, f'No study with 1–{max_files} files on the visible catalog page'
        study, count = candidates[0]
        self.app.open_explore()
        self.app.select_filter('Study/dbGaP_Accession', study)
        self.open_source()
        self.wait_for_total(count)
        return count

    def add_all_filtered(self, max_files=25):
        """Read the small filtered baseline before clicking Add All Filtered Files."""
        status = self.visible('PageStatus').inner_text()
        count = int(re.search(r'of\s+([\d,]+)', status, re.I)[1].replace(',', ''))
        assert 0 < count <= max_files, f'Filter to 1–{max_files} files before adding all; found {count}'
        records = self.snapshot(source=True)
        assert len(records) == count, 'Filtered source snapshot is incomplete'
        self.visible('AddAll').click()
        self.expected.update((record.identity, record) for record in records)
        self.app.ui.wait_idle()

    def verify_duplicate_addition(self):
        """Reselect the same source files after C3DC clears the submitted selection."""
        original = dict(self.selected)
        assert original and original.keys() <= self.expected.keys()
        self.selected.clear()
        self.select_files(len(original))
        assert self.selected.keys() == original.keys(), 'The duplicate-addition fixture selected different source files'
        self.add_selected()

    def export_menu(self):
        self.visible('Export').click()
        expect(self.control('Manifest')).to_be_visible()

    def download_manifest(self, report_name):
        self.export_menu()
        return self.save_download(lambda: self.control('Manifest').click(), report_name)

    def verify_manifest(self):
        assert self.manifest_path, 'Download a cart manifest first'
        rows = verify_csv_manifest(self.manifest_path, tuple(self.expected.values()), name_column='name',
                                   participant_column='Participant ID', required_columns=('drs_uri', 'Md5sum'))
        for row in rows:
            assert row['drs_uri'].startswith('drs://') and len(row['drs_uri'].split('/')[-1]) > 0, f'Invalid DRS URI: {row}'
            assert re.fullmatch(r'[a-fA-F0-9]{32}', row['Md5sum']), f'Invalid manifest MD5: {row}'
        self.app.results.append({'check': 'Cart manifest', 'status': 'PASSED', 'detail': f'{len(rows)} file names and participant sets matched; DRS/MD5 formats verified'})

    def remove_one(self):
        records = self.snapshot()
        assert records, 'Add a file before removing it'
        name = records[0].name
        table = self.visible('Table')
        while self.visible('Previous').is_enabled():
            self.move_page('Previous')
        row = table.locator('tbody tr').filter(has=self.app.page.get_by_text(name, exact=True))
        expect(row).to_have_count(1)
        self.control('RowRemove', row).click()
        del self.expected[records[0].identity]
        self.wait_for_total(len(self.expected))

    def remove_all(self, confirm):
        from Commons.static_data import _normalize_text
        count = len(self.expected)
        assert count, 'Add files before checking Remove All'
        self.visible('RemoveAll').click()
        dialog = self.visible('RemovalDialog')
        message = _normalize_text(dialog.inner_text())
        assert f'Remove All files ({count}) From Cart' in message, f'Unexpected removal confirmation: {message}'
        dialog.get_by_role('button', name='OK' if confirm else re.compile('^Cancel$', re.I)).click()
        expect(dialog).not_to_be_visible()
        if confirm:
            self.expected.clear()
        self.wait_for_total(len(self.expected))

    def verify_empty(self, report_name):
        assert not self.expected, 'Expected cart must be empty before empty-state verification'
        self.verify(report_name)
        expect(self.visible('Empty')).to_have_text('No Matching Records Found')
        expect(self.visible('Export')).to_be_disabled()
        expect(self.visible('Next')).to_be_disabled()
        expect(self.visible('Previous')).to_be_disabled()

    def verify_static(self):
        self.app.verify_static_data('FileCartPage')

    def verify_guide(self):
        from Commons.apps.c3dc.static_pages import open_guide_pdf, verify_user_guide_content
        open_guide_pdf(self.app, self.visible('Guide'))
        verify_user_guide_content(self.app)

    def verify_cgc_entry(self, expected_host):
        """Verify the unauthenticated CGC launch, then close before signing in."""
        from urllib.parse import urlparse
        assert expected_host, 'Supply the expected CGC login hostname in Params'
        self.export_menu()
        option = self.control('CGC')
        expect(option).to_be_enabled()
        with self.app.page.expect_popup(timeout=self.app.ui.timeout_ms) as event:
            option.click()
        popup = event.value
        try:
            popup.wait_for_url(re.compile(r'^https://' + re.escape(expected_host) + r'/auth/login(?:[?]|$)'),
                               wait_until='commit', timeout=self.app.ui.timeout_ms)
            assert urlparse(popup.url).hostname == expected_host
        finally:
            popup.close()
        self.app.results.append({'check': 'CGC export entry', 'status': 'PASSED', 'detail': 'Expected login destination opened; no authentication or external project submission'})
