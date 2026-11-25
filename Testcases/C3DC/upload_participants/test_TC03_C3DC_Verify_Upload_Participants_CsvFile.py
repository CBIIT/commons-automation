"""TC03_C3DC_Verify_Upload_Participants_CsvFile — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC03_C3DC_Verify_Upload_Participants_CsvFile(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.prepare_participant_upload(2, 1)
    c3dc.create_participant_upload_file('TC03_C3DC_Verify_Upload_Participants_CsvFile', 'participants.csv')
    c3dc.open_participant_upload()
    c3dc.attach_participant_file(None)
    c3dc.verify_upload_preview()
    c3dc.submit_participant_upload()
    c3dc.verify_uploaded_participants('TC03_C3DC_Verify_Upload_Participants_CsvFile')
    c3dc.assert_no_failures()
