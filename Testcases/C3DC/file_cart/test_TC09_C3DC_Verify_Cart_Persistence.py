"""TC09_C3DC_Verify_Cart_Persistence — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC09_C3DC_Verify_Cart_Persistence(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open_explore_files()
    c3dc.file_cart.select_files(3)
    c3dc.file_cart.add_selected()
    c3dc.file_cart.open()
    c3dc.file_cart.verify('TC09_C3DC_Verify_Cart_Persistence')
    c3dc.file_cart.verify_persistence('TC09_C3DC_Verify_Cart_Persistence')
    c3dc.assert_no_failures()
