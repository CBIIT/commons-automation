"""TC09_CTDC_Verify_Cart_Persistence — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC09_CTDC_Verify_Cart_Persistence(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC09_CTDC_Verify_Cart_Persistence')
    ctdc.file_cart.verify_persistence('TC09_CTDC_Verify_Cart_Persistence')
    ctdc.assert_no_failures()
