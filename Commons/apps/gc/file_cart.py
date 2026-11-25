"""GC file-cart navigation and explicit source/cart column mapping."""
import re

from playwright.sync_api import expect

from Commons import action_log
from Commons.file_cart import FileCart


class GCFileCart(FileCart):
    # ----------------------------------------------------------------------------
    # GC specification: rendering, column mappings, messages, and manifest schema
    # ----------------------------------------------------------------------------
    wait_for_page_rows = True
    wait_for_sorted_rows = True
    empty_message = 'No Matching Records Found'
    add_all_message = 'Are you sure to add All Files to cart'
    identity_fields = ('name', 'study', 'samples')
    source_columns = {'name': 'File Name', 'study': 'Accession', 'samples': 'Sample ID', 'type': 'File Type'}
    cart_columns = source_columns
    removal_message = 'Remove All files ({count}) From Cart'
    removal_confirm, removal_cancel = 'OK', 'Cancel'
    manifest_required = ('drs_uri', 'Md5sum', 'Accession', 'Sample Id')

    # ----------------------------------------------------------------------------
    # Source selection: choose files with distinguishable cart metadata
    # ----------------------------------------------------------------------------
    def select_files(self, count=3):
        """Choose distinguishable cart rows; GC does not display its source File ID.

        Distinct IDs may share every displayed cart field. Do not silently merge
        them: partial fixtures choose distinct metadata, and full-page fixtures
        advance to a page whose rows can all be compared independently.
        """
        assert count >= 0
        if count == 0:
            for _ in range(self.app.MAX_PAGES):
                rows = self.read_page(source=True)
                if len({r.identity for r in rows}) == len(rows) and not set(self.selected) & {r.identity for r in rows}:
                    return super().select_files(0)
                assert self.visible('SourceNext').is_enabled(), 'No distinguishable full source page available'
                self.move_page('Next', source=True)
            raise AssertionError('No unambiguous source page within the page guard')
        rows = self.read_page(source=True)
        chosen = {}
        for index, record in enumerate(rows):
            if record.identity not in chosen and record.identity not in self.selected:
                chosen[record.identity] = (index, record)
            if len(chosen) == count:
                break
        assert len(chosen) == count, f'Need {count} distinguishable source rows; found {len(chosen)}'
        for index, record in chosen.values():
            self.visible('SourceTable').locator('tbody tr').nth(index).locator('input[type=checkbox]').check()
            self.selected[record.identity] = record
        action_log.ui_action(f'Selected {len(chosen)} distinguishable GC source files.')

    # ----------------------------------------------------------------------------
    # Manifest export: download directly from the cart toolbar
    # ----------------------------------------------------------------------------
    def download_manifest(self, report_name):
        # GC places Download Manifest beside the menu rather than inside it.
        return self.save_download(lambda: self.visible('Manifest').click(), report_name)

    # ----------------------------------------------------------------------------
    # Filtering: find a bounded study and apply its accession filter
    # ----------------------------------------------------------------------------
    def prepare_small_filter(self, max_files=25):
        """Find a small live study from the catalog instead of embedding an accession."""
        self.app.open_studies_listing()
        table = self.visible('Catalog')
        expect(table.locator('tbody tr').first).to_be_visible(timeout=self.app.ui.timeout_ms)
        known = self.app.repo.filter_group('StudyFacet/PHS_Accession').checkboxes
        for _ in range(self.app.MAX_PAGES):
            data = table.evaluate("""t=>({headers:[...t.querySelectorAll('thead th')].map(x=>x.innerText.trim()),
                rows:[...t.querySelectorAll('tbody tr')].map(r=>[...r.cells].map(x=>x.innerText.trim()))})""")
            headers = [' '.join(h.split()) for h in data['headers']]
            study_col, count_col = headers.index('Study'), headers.index('Number of Files')
            candidates = [(r[study_col], int(r[count_col].replace(',', ''))) for r in data['rows']
                          if r[study_col] in known and r[count_col].replace(',', '').isdigit()
                          and 0 < int(r[count_col].replace(',', '')) <= max_files]
            if candidates:
                study, count = candidates[0]
                self.app.open_data()
                # QA and QA2 label this facet differently; both observed IDs live in YAML.
                facet = self.visible('StudyFacet')
                if facet.get_attribute('aria-expanded') == 'false':
                    facet.click()
                dropdown = self.visible('StudyAccession')
                if dropdown.get_attribute('aria-expanded') != 'true':
                    dropdown.click()
                self.visible('StudySearch').fill(study)
                checkbox = self.app.repo.xpath('FileCart/StudyCheckbox').replace('{value}', study)
                self.app.ui.visible(checkbox).click()
                self.app.ui.wait_idle()
                self.open_explore_files()
                self.wait_for_total(count)
                return count
            next_page = self.visible('CatalogNext')
            assert next_page.is_enabled(), f'No catalog study with 1–{max_files} files'
            before = table.inner_text()
            next_page.click()
            expect(table).not_to_have_text(before)
        raise AssertionError('Catalog exceeded configured page guard')

    # ----------------------------------------------------------------------------
    # Source navigation: open the Files tab and reset selection
    # ----------------------------------------------------------------------------
    def open_explore_files(self):
        self.app.open_data()
        expect(self.app.page.locator(self.app.repo.xpath('FileCart/SourceTab'))).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.app.click('FileCart/SourceTab')
        self.selected.clear()
        expect(self.visible('SourceTable').locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)
