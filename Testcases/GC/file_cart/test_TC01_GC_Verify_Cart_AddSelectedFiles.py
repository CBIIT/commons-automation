"""TC01_GC_Verify_Cart_AddSelectedFiles — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_Verify_Cart_AddSelectedFiles(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(3)
    gc.file_cart.move_page('Next', source=True)
    gc.file_cart.select_files(2)
    gc.file_cart.add_selected()
    gc.file_cart.open()
    gc.file_cart.verify('TC01_GC_Verify_Cart_AddSelectedFiles')
    gc.assert_no_failures()
