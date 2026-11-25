"""TC02_C3DC_Verify_Cart_AddAllFilteredFiles — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC02_C3DC_Verify_Cart_AddAllFilteredFiles(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.prepare_small_filter(25)
    c3dc.file_cart.add_all_filtered(25)
    c3dc.file_cart.open()
    c3dc.file_cart.verify('TC02_C3DC_Verify_Cart_AddAllFilteredFiles')
    c3dc.assert_no_failures()
