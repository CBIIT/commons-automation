"""GC file-cart navigation and explicit source/cart column mapping."""
from playwright.sync_api import expect
from Commons.file_cart import FileCart


class GCFileCart(FileCart):
    identity_fields = ('name', 'study', 'samples')
    source_columns = {'name': 'File Name', 'study': 'Accession', 'samples': 'Sample ID', 'type': 'File Type'}
    cart_columns = source_columns

    def open_source(self):
        self.app.open_data()
        expect(self.app.page.locator(self.app.repo.xpath('FileCart/SourceTab'))).to_be_visible(timeout=self.app.ui.timeout_ms)
        self.app.click('FileCart/SourceTab')
        self.selected.clear()
        expect(self.visible('SourceTable').locator('tbody input[type=checkbox]').first).to_be_visible(timeout=self.app.ui.timeout_ms)
