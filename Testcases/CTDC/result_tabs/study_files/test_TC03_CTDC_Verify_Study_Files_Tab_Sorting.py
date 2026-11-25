"""TC03_CTDC_Verify_Study_Files_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC03_CTDC_Verify_Study_Files_Tab_Sorting(ctdc):
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_filter('Studies/Study', 'CMB')
    ctdc.verify_result_tab_sorting('Study Files', 'TC03_CTDC_Verify_Study_Files_Tab_Sorting')
    ctdc.assert_no_failures()
