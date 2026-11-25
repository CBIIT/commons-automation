"""TC02_C3DC_Verify_Participants_Tab_JSON_Download — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC02_C3DC_Verify_Participants_Tab_JSON_Download(c3dc):
    c3dc.load_query_file('C3DC_ResultTabDownloads.xlsx')
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Diagnosis/Diagnosis', 'AbdominalFibromatosis')
    c3dc.result_tabs.download('Participants', 'JSON', 'TC02_C3DC_Verify_Participants_Tab_JSON_Download')
    c3dc.result_tabs.verify_download('Participants', 'JSON')
    c3dc.assert_no_failures()
