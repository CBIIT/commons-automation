"""TC12_GC_Verify_Cart_CGC_ExportEntry — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC12_GC_Verify_Cart_CGC_ExportEntry(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(3)
    gc.file_cart.add_selected()
    gc.file_cart.open()
    gc.file_cart.verify('TC12_GC_Verify_Cart_CGC_ExportEntry')
    gc.file_cart.verify_cgc_entry('cgc-accounts.sbgenomics.com')
    gc.file_cart.verify('TC12_GC_Verify_Cart_CGC_ExportEntry')
    gc.assert_no_failures()
