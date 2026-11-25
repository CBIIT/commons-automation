"""TC01_C3DC_Verify_HomePage_Content — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.static
def test_TC01_C3DC_Verify_HomePage_Content(c3dc):
    c3dc.accept_banner()
    c3dc.open_home_page()
    c3dc.verify_home_page_content()
    c3dc.assert_no_failures()
