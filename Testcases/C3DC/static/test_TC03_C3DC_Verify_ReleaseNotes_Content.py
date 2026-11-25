"""TC03_C3DC_Verify_ReleaseNotes_Content — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.static
def test_TC03_C3DC_Verify_ReleaseNotes_Content(c3dc):
    c3dc.accept_banner()
    c3dc.open_release_notes()
    c3dc.verify_release_notes_content()
    c3dc.assert_no_failures()
