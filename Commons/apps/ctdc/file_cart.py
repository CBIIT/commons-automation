"""CTDC file-cart navigation and explicit source/cart column mapping."""
from playwright.sync_api import expect
from Commons.file_cart import FileCart


class CTDCFileCart(FileCart):
    # ----------------------------------------------------------------------------
    # CTDC specification: rendering, column mappings, messages, and manifest schema
    # ----------------------------------------------------------------------------
    wait_for_page_rows = True
    wait_for_sorted_rows = True
    clears_source_selection = True
    identity_fields = ('name', 'participants', 'samples')
    source_columns = {'name': 'File Name', 'format': 'Format', 'type': 'File Type', 'participants': 'Participant ID', 'samples': 'Specimen Record ID', 'size': 'Size'}
    cart_columns = source_columns
    add_all_message = 'Add all {count} files to My Files?'
    empty_message = 'No files have been added to the cart'
    manifest_participants = 'participant_id'
    manifest_required = ('drs_uri', 'Md5sum')
    removal_message = '{count} File(s) will be removed from your cart'

    # ----------------------------------------------------------------------------
    # Participant files: open the Files tab and restore participant/sample mappings
    # ----------------------------------------------------------------------------
    def open_explore_files(self):
        self.source_columns = type(self).source_columns
        self.identity_fields = type(self).identity_fields
        self.app.open_explore()
        expect(self.app.page.locator(self.app.repo.xpath('FileCart/SourceTab'))).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.app.click('FileCart/SourceTab')
        self.selected.clear()
        expect(self.visible('SourceTable').locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)

    # ----------------------------------------------------------------------------
    # Study files: switch source and use the study-file column mappings
    # ----------------------------------------------------------------------------
    def open_study_source(self):
        """Study files are a bounded source without participant/sample columns."""
        self.open_explore_files()
        self.visible('StudySourceTab').click()
        expect(self.visible('SourceTable').locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.source_columns = {'name': 'File Name', 'format': 'Format', 'type': 'File Type'}
        self.identity_fields = ('name',)
