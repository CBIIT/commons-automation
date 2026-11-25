"""TC08_ICDC_Verify_Cart_RemoveAllFiles — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC08_ICDC_Verify_Cart_RemoveAllFiles(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC08_ICDC_Verify_Cart_RemoveAllFiles')
    icdc.file_cart.remove_all(False)
    icdc.file_cart.verify('TC08_ICDC_Verify_Cart_RemoveAllFiles')
    icdc.file_cart.remove_all(True)
    icdc.file_cart.verify_empty('TC08_ICDC_Verify_Cart_RemoveAllFiles')
    icdc.file_cart.verify_persistence('TC08_ICDC_Verify_Cart_RemoveAllFiles')
    icdc.assert_no_failures()
