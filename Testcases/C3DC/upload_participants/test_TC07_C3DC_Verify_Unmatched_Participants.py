"""TC07_C3DC_Verify_Unmatched_Participants — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC07_C3DC_Verify_Unmatched_Participants(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.verify_unmatched_participants(3, 'TC07_C3DC_Verify_Unmatched_Participants')
    c3dc.assert_no_failures()
