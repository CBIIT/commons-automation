"""TC03_CTDC_Verify_Participants_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC03_CTDC_Verify_Participants_Tab_Sorting(ctdc):
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_filter('Studies/Study', 'CMB')
    ctdc.select_filter('Participants/Diagnosis', 'SmallCellLung')
    ctdc.verify_result_tab_sorting('Participants', 'TC03_CTDC_Verify_Participants_Tab_Sorting')
    ctdc.assert_no_failures()
