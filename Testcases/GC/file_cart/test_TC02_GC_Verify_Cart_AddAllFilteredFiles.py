"""TC02_GC_Verify_Cart_AddAllFilteredFiles — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_Verify_Cart_AddAllFilteredFiles(gc):
    gc.accept_banner()
    gc.file_cart.prepare_small_filter(100)
    gc.file_cart.add_all_filtered(100)
    gc.file_cart.open()
    gc.file_cart.verify('TC02_GC_Verify_Cart_AddAllFilteredFiles')
    gc.assert_no_failures()
