"""TC03_PSDC_Study_Pbcs_CancerTypes-NotApplicable — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC03_PSDC_Study_Pbcs_CancerTypes_NotApplicable(psdc):
    psdc.load_query_file('TC03_PSDC_Study_Pbcs_CancerTypes-NotApplicable.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Studies/CancerTypes', 'Not Applicable')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
