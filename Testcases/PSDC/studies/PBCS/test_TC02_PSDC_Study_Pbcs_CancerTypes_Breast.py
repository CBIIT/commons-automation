"""TC02_PSDC_Study_Pbcs_CancerTypes-Breast — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC02_PSDC_Study_Pbcs_CancerTypes_Breast(psdc):
    psdc.load_query_file('TC02_PSDC_Study_Pbcs_CancerTypes-Breast.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Studies/CancerTypes', 'breast')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
