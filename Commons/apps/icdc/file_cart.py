"""ICDC file-cart navigation and explicit source/cart column mapping."""
from playwright.sync_api import expect
from Commons.file_cart import FileCart


class ICDCFileCart(FileCart):
    # ----------------------------------------------------------------------------
    # ICDC specification: rendering, column mappings, messages, and manifest schema
    # ----------------------------------------------------------------------------
    wait_for_page_rows = True
    wait_for_sorted_rows = True
    add_all_message = 'Are you sure to add All Files to cart'
    clears_source_selection = True
    identity_fields = ('name', 'participants', 'samples')
    source_columns = {'name': 'File Name', 'participants': 'Case ID', 'samples': 'Sample ID', 'format': 'Format', 'type': 'File Type', 'size': 'Size'}
    cart_columns = source_columns
    empty_message = 'No files have been added to the cart'
    manifest_participants = 'Case ID'
    manifest_required = ('drs_uri', 'md5sum')
    removal_message = 'Remove All files ({count}) From Cart'
    removal_confirm, removal_cancel = 'OK', 'Cancel'

    # ----------------------------------------------------------------------------
    # Case files: open the Files tab and restore case/sample mappings
    # ----------------------------------------------------------------------------
    def open_source(self):
        self.source_columns = type(self).source_columns
        self.identity_fields = type(self).identity_fields
        self.app.open_cases()
        expect(self.app.page.locator(self.app.repo.xpath('FileCart/SourceTab'))).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.app.click('FileCart/SourceTab')
        self.selected.clear()
        expect(self.visible('SourceTable').locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)

    # ----------------------------------------------------------------------------
    # Study files: switch source and use the study-file column mappings
    # ----------------------------------------------------------------------------
    def open_study_source(self):
        """Study files are a bounded source without participant/sample columns."""
        self.open_source()
        self.visible('StudySourceTab').click()
        expect(self.visible('SourceTable').locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.source_columns = {'name': 'File Name', 'format': 'Format', 'type': 'File Type'}
        self.identity_fields = ('name',)
