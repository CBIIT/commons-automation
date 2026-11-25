"""TC06_C3DC_Verify_ExploreUserGuide_Content — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.static
def test_TC06_C3DC_Verify_ExploreUserGuide_Content(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.verify_explore_help_content('ExploreUserGuidePage')
    c3dc.assert_no_failures()
