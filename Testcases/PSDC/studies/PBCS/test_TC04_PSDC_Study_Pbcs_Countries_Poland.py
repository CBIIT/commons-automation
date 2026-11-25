"""TC04_PSDC_Study_Pbcs_Countries-Poland — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC04_PSDC_Study_Pbcs_Countries_Poland(psdc):
    psdc.load_query_file('TC04_PSDC_Study_Pbcs_Countries-Poland.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Studies/Countries', 'Poland')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
