"""TC05_ICDC_Verify_Cart_Pagination — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC05_ICDC_Verify_Cart_Pagination(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(0)
    icdc.file_cart.add_selected()
    icdc.file_cart.move_page('Next', source=True)
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.set_page_size(10)
    icdc.file_cart.verify('TC05_ICDC_Verify_Cart_Pagination')
    icdc.file_cart.set_page_size(25)
    icdc.file_cart.verify('TC05_ICDC_Verify_Cart_Pagination')
    icdc.assert_no_failures()
