"""TC07_CTDC_Verify_Cart_RemoveFile — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC07_CTDC_Verify_Cart_RemoveFile(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC07_CTDC_Verify_Cart_RemoveFile')
    ctdc.file_cart.remove_one()
    ctdc.file_cart.verify('TC07_CTDC_Verify_Cart_RemoveFile')
    ctdc.file_cart.verify_persistence('TC07_CTDC_Verify_Cart_RemoveFile')
    ctdc.assert_no_failures()
