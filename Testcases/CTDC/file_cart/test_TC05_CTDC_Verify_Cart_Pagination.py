"""TC05_CTDC_Verify_Cart_Pagination — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC05_CTDC_Verify_Cart_Pagination(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(0)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.move_page('Next', source=True)
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.set_page_size(10)
    ctdc.file_cart.verify('TC05_CTDC_Verify_Cart_Pagination')
    ctdc.file_cart.set_page_size(25)
    ctdc.file_cart.verify('TC05_CTDC_Verify_Cart_Pagination')
    ctdc.assert_no_failures()
