"""TC13_CTDC_Verify_Cart_SelectedFiles_Manifest — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC13_CTDC_Verify_Cart_SelectedFiles_Manifest(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC13_CTDC_Verify_Cart_SelectedFiles_Manifest')
    ctdc.file_cart.verify_selected_export('TC13_CTDC_Verify_Cart_SelectedFiles_Manifest', 2)
    ctdc.assert_no_failures()
