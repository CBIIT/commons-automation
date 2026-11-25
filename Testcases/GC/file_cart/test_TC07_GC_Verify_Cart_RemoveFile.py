"""TC07_GC_Verify_Cart_RemoveFile — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC07_GC_Verify_Cart_RemoveFile(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(3)
    gc.file_cart.add_selected()
    gc.file_cart.open()
    gc.file_cart.verify('TC07_GC_Verify_Cart_RemoveFile')
    gc.file_cart.remove_one()
    gc.file_cart.verify('TC07_GC_Verify_Cart_RemoveFile')
    gc.file_cart.verify_persistence('TC07_GC_Verify_Cart_RemoveFile')
    gc.assert_no_failures()
