"""TC05_GC_Verify_Cart_Pagination — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_Verify_Cart_Pagination(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(0)
    gc.file_cart.add_selected()
    gc.file_cart.move_page('Next', source=True)
    gc.file_cart.select_files(3)
    gc.file_cart.add_selected()
    gc.file_cart.open()
    gc.file_cart.set_page_size(10)
    gc.file_cart.verify('TC05_GC_Verify_Cart_Pagination')
    gc.file_cart.set_page_size(25)
    gc.file_cart.verify('TC05_GC_Verify_Cart_Pagination')
    gc.assert_no_failures()
