"""TC09_ICDC_Verify_Cart_Persistence — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC09_ICDC_Verify_Cart_Persistence(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC09_ICDC_Verify_Cart_Persistence')
    icdc.file_cart.verify_persistence('TC09_ICDC_Verify_Cart_Persistence')
    icdc.assert_no_failures()
