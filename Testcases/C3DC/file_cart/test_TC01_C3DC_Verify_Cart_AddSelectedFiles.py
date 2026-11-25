"""TC01_C3DC_Verify_Cart_AddSelectedFiles — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC01_C3DC_Verify_Cart_AddSelectedFiles(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open_explore_files()
    c3dc.file_cart.select_files(3)
    c3dc.file_cart.move_page('Next', source=True)
    c3dc.file_cart.select_files(2)
    c3dc.file_cart.add_selected()
    c3dc.file_cart.open()
    c3dc.file_cart.verify('TC01_C3DC_Verify_Cart_AddSelectedFiles')
    c3dc.assert_no_failures()
