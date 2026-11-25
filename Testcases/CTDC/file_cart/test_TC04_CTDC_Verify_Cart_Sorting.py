"""TC04_CTDC_Verify_Cart_Sorting — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC04_CTDC_Verify_Cart_Sorting(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC04_CTDC_Verify_Cart_Sorting')
    ctdc.file_cart.verify_sort('name', 'asc')
    ctdc.file_cart.verify_sort('name', 'desc')
    ctdc.file_cart.verify_sort('type', 'asc')
    ctdc.file_cart.verify_sort('type', 'desc')
    ctdc.file_cart.verify_sort('size', 'asc')
    ctdc.file_cart.verify_sort('size', 'desc')
    ctdc.file_cart.verify('TC04_CTDC_Verify_Cart_Sorting')
    ctdc.assert_no_failures()
