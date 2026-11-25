"""TC07_C3DC_Verify_Cart_RemoveFile — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC07_C3DC_Verify_Cart_RemoveFile(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open_explore_files()
    c3dc.file_cart.select_files(3)
    c3dc.file_cart.add_selected()
    c3dc.file_cart.open()
    c3dc.file_cart.verify('TC07_C3DC_Verify_Cart_RemoveFile')
    c3dc.file_cart.remove_one()
    c3dc.file_cart.verify('TC07_C3DC_Verify_Cart_RemoveFile')
    c3dc.file_cart.verify_persistence('TC07_C3DC_Verify_Cart_RemoveFile')
    c3dc.assert_no_failures()
