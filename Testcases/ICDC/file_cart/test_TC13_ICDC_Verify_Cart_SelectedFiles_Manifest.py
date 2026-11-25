"""TC13_ICDC_Verify_Cart_SelectedFiles_Manifest — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC13_ICDC_Verify_Cart_SelectedFiles_Manifest(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC13_ICDC_Verify_Cart_SelectedFiles_Manifest')
    icdc.file_cart.verify_selected_export('TC13_ICDC_Verify_Cart_SelectedFiles_Manifest', 2)
    icdc.assert_no_failures()
