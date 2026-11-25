"""TC05_C3DC_Verify_Cart_Pagination — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC05_C3DC_Verify_Cart_Pagination(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open_explore_files()
    c3dc.file_cart.select_files(0)
    c3dc.file_cart.add_selected()
    c3dc.file_cart.move_page('Next', source=True)
    c3dc.file_cart.select_files(3)
    c3dc.file_cart.add_selected()
    c3dc.file_cart.open()
    c3dc.file_cart.set_page_size(10)
    c3dc.file_cart.verify('TC05_C3DC_Verify_Cart_Pagination')
    c3dc.file_cart.set_page_size(25)
    c3dc.file_cart.verify('TC05_C3DC_Verify_Cart_Pagination')
    c3dc.file_cart.set_page_size(50)
    c3dc.file_cart.verify('TC05_C3DC_Verify_Cart_Pagination')
    c3dc.assert_no_failures()
