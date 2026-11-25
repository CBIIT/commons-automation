"""TC03_GC_Verify_Cart_DuplicateAddition — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_Verify_Cart_DuplicateAddition(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(3)
    gc.file_cart.add_selected()
    gc.file_cart.verify_duplicate_addition()
    gc.file_cart.open()
    gc.file_cart.verify('TC03_GC_Verify_Cart_DuplicateAddition')
    gc.assert_no_failures()
