"""TC01_C3DC_Verify_Upload_Participants_TypedIDs — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC01_C3DC_Verify_Upload_Participants_TypedIDs(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.prepare_participant_upload(2, 1)
    c3dc.open_participant_upload()
    c3dc.type_participant_ids(None)
    c3dc.verify_upload_preview()
    c3dc.submit_participant_upload()
    c3dc.verify_uploaded_participants('TC01_C3DC_Verify_Upload_Participants_TypedIDs')
    c3dc.assert_no_failures()
