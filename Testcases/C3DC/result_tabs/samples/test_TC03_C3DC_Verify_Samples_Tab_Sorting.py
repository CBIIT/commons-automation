"""TC03_C3DC_Verify_Samples_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC03_C3DC_Verify_Samples_Tab_Sorting(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Diagnosis/Diagnosis', 'AbdominalFibromatosis')
    c3dc.verify_result_tab_sorting('Samples', 'TC03_C3DC_Verify_Samples_Tab_Sorting')
    c3dc.assert_no_failures()
