"""TC03_CTDC_Verify_Cart_DuplicateAddition — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC03_CTDC_Verify_Cart_DuplicateAddition(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.verify_duplicate_addition()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC03_CTDC_Verify_Cart_DuplicateAddition')
    ctdc.assert_no_failures()
