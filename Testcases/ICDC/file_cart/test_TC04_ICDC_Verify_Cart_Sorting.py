"""TC04_ICDC_Verify_Cart_Sorting — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC04_ICDC_Verify_Cart_Sorting(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC04_ICDC_Verify_Cart_Sorting')
    icdc.file_cart.verify_sort('name', 'asc')
    icdc.file_cart.verify_sort('name', 'desc')
    icdc.file_cart.verify_sort('type', 'asc')
    icdc.file_cart.verify_sort('type', 'desc')
    icdc.file_cart.verify_sort('size', 'asc')
    icdc.file_cart.verify_sort('size', 'desc')
    icdc.file_cart.verify('TC04_ICDC_Verify_Cart_Sorting')
    icdc.assert_no_failures()
