"""TC05_C3DC_Verify_NotesToUser_Content — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.static
def test_TC05_C3DC_Verify_NotesToUser_Content(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.verify_explore_help_content('NotesToUserPage')
    c3dc.assert_no_failures()
