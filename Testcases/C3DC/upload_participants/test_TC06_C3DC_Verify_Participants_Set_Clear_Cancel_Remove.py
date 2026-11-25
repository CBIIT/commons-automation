"""TC06_C3DC_Verify_Participants_Set_Clear_Cancel_Remove — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC06_C3DC_Verify_Participants_Set_Clear_Cancel_Remove(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.remember_participant_upload_baseline()
    c3dc.prepare_participant_upload_update(2, 1)
    c3dc.open_participant_upload()
    c3dc.type_participant_ids(None)
    c3dc.verify_upload_preview()
    c3dc.clear_participant_upload()
    c3dc.verify_participant_upload_cleared()
    c3dc.open_participant_upload()
    c3dc.verify_participant_upload_empty()
    c3dc.type_participant_ids(None)
    c3dc.verify_upload_preview()
    c3dc.submit_participant_upload()
    c3dc.verify_uploaded_participants('TC06_C3DC_Verify_Participants_Set_Clear_Cancel_Remove')
    c3dc.open_participant_upload()
    c3dc.type_replacement_participant_ids()
    c3dc.cancel_participant_upload()
    c3dc.verify_uploaded_participants('TC06_C3DC_Verify_Participants_Set_Clear_Cancel_Remove')
    c3dc.open_participant_upload()
    c3dc.type_replacement_participant_ids()
    c3dc.close_participant_upload()
    c3dc.verify_uploaded_participants('TC06_C3DC_Verify_Participants_Set_Clear_Cancel_Remove')
    c3dc.remove_participant_upload()
    c3dc.verify_participant_upload_cleared()
    c3dc.assert_no_failures()
