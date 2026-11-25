"""TC04_C3DC_Verify_Cart_Sorting — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC04_C3DC_Verify_Cart_Sorting(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open_explore_files()
    c3dc.file_cart.select_files(3)
    c3dc.file_cart.add_selected()
    c3dc.file_cart.open()
    c3dc.file_cart.verify('TC04_C3DC_Verify_Cart_Sorting')
    c3dc.file_cart.verify_sort('name', 'asc')
    c3dc.file_cart.verify_sort('name', 'desc')
    c3dc.file_cart.verify_sort('study', 'asc')
    c3dc.file_cart.verify_sort('study', 'desc')
    c3dc.file_cart.verify_sort('size', 'asc')
    c3dc.file_cart.verify_sort('size', 'desc')
    c3dc.file_cart.verify('TC04_C3DC_Verify_Cart_Sorting')
    c3dc.assert_no_failures()
