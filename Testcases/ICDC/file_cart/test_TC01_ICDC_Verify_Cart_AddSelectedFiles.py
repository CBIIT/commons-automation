"""TC01_ICDC_Verify_Cart_AddSelectedFiles — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC01_ICDC_Verify_Cart_AddSelectedFiles(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.move_page('Next', source=True)
    icdc.file_cart.select_files(2)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC01_ICDC_Verify_Cart_AddSelectedFiles')
    icdc.assert_no_failures()
