"""TC02_PSDC_Study_Plco_CancerTypes-ProstateGland — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC02_PSDC_Study_Plco_CancerTypes_ProstateGland(psdc):
    psdc.load_query_file('TC02_PSDC_Study_Plco_CancerTypes-ProstateGland.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PLCO')
    psdc.select_filter('Studies/CancerTypes', 'prostate gland')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
