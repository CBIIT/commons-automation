"""TC08_CTDC_Verify_Cart_RemoveAllFiles — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC08_CTDC_Verify_Cart_RemoveAllFiles(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC08_CTDC_Verify_Cart_RemoveAllFiles')
    ctdc.file_cart.remove_all(False)
    ctdc.file_cart.verify('TC08_CTDC_Verify_Cart_RemoveAllFiles')
    ctdc.file_cart.remove_all(True)
    ctdc.file_cart.verify_empty('TC08_CTDC_Verify_Cart_RemoveAllFiles')
    ctdc.file_cart.verify_persistence('TC08_CTDC_Verify_Cart_RemoveAllFiles')
    ctdc.assert_no_failures()
