"""TC05_C3DC_Verify_View_Update_Participants_Set — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC05_C3DC_Verify_View_Update_Participants_Set(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.prepare_participant_upload_update(2, 1)
    c3dc.open_participant_upload()
    c3dc.type_participant_ids(None)
    c3dc.verify_upload_preview()
    c3dc.submit_participant_upload()
    c3dc.verify_uploaded_participants('TC05_C3DC_Verify_View_Update_Participants_Set')
    c3dc.open_participant_upload()
    c3dc.verify_participant_upload_draft(None)
    c3dc.verify_upload_preview()
    c3dc.use_replacement_participant_upload()
    c3dc.type_participant_ids(None)
    c3dc.verify_upload_preview()
    c3dc.submit_participant_upload()
    c3dc.verify_uploaded_participants('TC05_C3DC_Verify_View_Update_Participants_Set')
    c3dc.open_participant_upload()
    c3dc.verify_participant_upload_draft(None)
    c3dc.verify_upload_preview()
    c3dc.cancel_participant_upload()
    c3dc.assert_no_failures()
