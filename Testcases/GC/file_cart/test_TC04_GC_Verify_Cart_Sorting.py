"""TC04_GC_Verify_Cart_Sorting — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_Verify_Cart_Sorting(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(3)
    gc.file_cart.add_selected()
    gc.file_cart.open()
    gc.file_cart.verify('TC04_GC_Verify_Cart_Sorting')
    gc.file_cart.verify_sort('name', 'asc')
    gc.file_cart.verify_sort('name', 'desc')
    gc.file_cart.verify_sort('type', 'asc')
    gc.file_cart.verify_sort('type', 'desc')
    gc.file_cart.verify('TC04_GC_Verify_Cart_Sorting')
    gc.assert_no_failures()
