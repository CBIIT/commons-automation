"""TC10_C3DC_Verify_Cart_StaticContent_UserGuide — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC10_C3DC_Verify_Cart_StaticContent_UserGuide(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open()
    c3dc.file_cart.verify_static()
    c3dc.file_cart.verify_guide()
    c3dc.assert_no_failures()
