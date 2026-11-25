"""TC04_C3DC_Verify_UserGuide_Content — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.static
def test_TC04_C3DC_Verify_UserGuide_Content(c3dc):
    c3dc.accept_banner()
    c3dc.open_user_guide()
    c3dc.verify_user_guide_content()
    c3dc.assert_no_failures()
