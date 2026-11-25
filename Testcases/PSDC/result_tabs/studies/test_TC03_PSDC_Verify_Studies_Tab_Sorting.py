"""TC03_PSDC_Verify_Studies_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC03_PSDC_Verify_Studies_Tab_Sorting(psdc):
    psdc.accept_banner()
    psdc.open_explore()
    psdc.verify_result_tab_sorting('Studies', 'TC03_PSDC_Verify_Studies_Tab_Sorting')
    psdc.assert_no_failures()
