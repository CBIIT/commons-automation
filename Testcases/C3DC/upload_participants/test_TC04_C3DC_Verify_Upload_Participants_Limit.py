"""TC04_C3DC_Verify_Upload_Participants_Limit — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC04_C3DC_Verify_Upload_Participants_Limit(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.verify_participant_upload_limit(1500, 'TC04_C3DC_Verify_Upload_Participants_Limit')
    c3dc.assert_no_failures()
