"""TC02_PSDC_Study_Nlst_CancerTypes-Lung — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC02_PSDC_Study_Nlst_CancerTypes_Lung(psdc):
    psdc.load_query_file('TC02_PSDC_Study_Nlst_CancerTypes-Lung.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('NLST')
    psdc.select_filter('Studies/CancerTypes', 'lung')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
