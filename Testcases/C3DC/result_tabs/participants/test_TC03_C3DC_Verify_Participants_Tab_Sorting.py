"""TC03_C3DC_Verify_Participants_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC03_C3DC_Verify_Participants_Tab_Sorting(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Diagnosis/Diagnosis', 'AbdominalFibromatosis')
    c3dc.verify_result_tab_sorting('Participants', 'TC03_C3DC_Verify_Participants_Tab_Sorting')
    c3dc.assert_no_failures()
