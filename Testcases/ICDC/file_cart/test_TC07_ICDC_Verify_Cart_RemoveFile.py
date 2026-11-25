"""TC07_ICDC_Verify_Cart_RemoveFile — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC07_ICDC_Verify_Cart_RemoveFile(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC07_ICDC_Verify_Cart_RemoveFile')
    icdc.file_cart.remove_one()
    icdc.file_cart.verify('TC07_ICDC_Verify_Cart_RemoveFile')
    icdc.file_cart.verify_persistence('TC07_ICDC_Verify_Cart_RemoveFile')
    icdc.assert_no_failures()
