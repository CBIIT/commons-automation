"""TC08_GC_Verify_Cart_RemoveAllFiles — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC08_GC_Verify_Cart_RemoveAllFiles(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(3)
    gc.file_cart.add_selected()
    gc.file_cart.open()
    gc.file_cart.verify('TC08_GC_Verify_Cart_RemoveAllFiles')
    gc.file_cart.remove_all(False)
    gc.file_cart.verify('TC08_GC_Verify_Cart_RemoveAllFiles')
    gc.file_cart.remove_all(True)
    gc.file_cart.verify_empty('TC08_GC_Verify_Cart_RemoveAllFiles')
    gc.file_cart.verify_persistence('TC08_GC_Verify_Cart_RemoveAllFiles')
    gc.assert_no_failures()
