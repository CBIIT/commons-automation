"""TC02_C3DC_Verify_AboutPage_Content — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.static
def test_TC02_C3DC_Verify_AboutPage_Content(c3dc):
    c3dc.accept_banner()
    c3dc.open_about_page()
    c3dc.verify_about_page_content()
    c3dc.assert_no_failures()
