"""TC03_ICDC_Verify_Cart_DuplicateAddition — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC03_ICDC_Verify_Cart_DuplicateAddition(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.verify_duplicate_addition()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC03_ICDC_Verify_Cart_DuplicateAddition')
    icdc.assert_no_failures()
