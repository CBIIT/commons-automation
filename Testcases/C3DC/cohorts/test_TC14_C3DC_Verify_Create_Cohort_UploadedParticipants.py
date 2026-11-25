"""TC14_C3DC_Verify_Create_Cohort_UploadedParticipants — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC14_C3DC_Verify_Create_Cohort_UploadedParticipants(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.prepare_participant_upload(3, 0)
    c3dc.open_participant_upload()
    c3dc.type_participant_ids(None)
    c3dc.verify_upload_preview()
    c3dc.submit_participant_upload()
    c3dc.verify_uploaded_participants('TC14_C3DC_Verify_Create_Cohort_UploadedParticipants')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_uploaded_cohort_participants()
    c3dc.assert_no_failures()
