"""TC01_CTDC_Verify_Cart_AddSelectedFiles — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC01_CTDC_Verify_Cart_AddSelectedFiles(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.move_page('Next', source=True)
    ctdc.file_cart.select_files(2)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC01_CTDC_Verify_Cart_AddSelectedFiles')
    ctdc.assert_no_failures()
