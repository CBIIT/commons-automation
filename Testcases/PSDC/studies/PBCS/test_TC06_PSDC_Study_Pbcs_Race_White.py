"""TC06_PSDC_Study_Pbcs_Race-White — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC06_PSDC_Study_Pbcs_Race_White(psdc):
    psdc.load_query_file('TC06_PSDC_Study_Pbcs_Race-White.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Participants/Race', 'white')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
