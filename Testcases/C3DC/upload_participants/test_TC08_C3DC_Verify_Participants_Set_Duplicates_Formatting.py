"""TC08_C3DC_Verify_Participants_Set_Duplicates_Formatting — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC08_C3DC_Verify_Participants_Set_Duplicates_Formatting(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.prepare_participant_upload(2, 0)
    c3dc.open_participant_upload()
    c3dc.type_formatted_participant_ids(2)
    c3dc.verify_upload_preview()
    c3dc.submit_participant_upload()
    c3dc.verify_uploaded_participants('TC08_C3DC_Verify_Participants_Set_Duplicates_Formatting')
    c3dc.assert_no_failures()
