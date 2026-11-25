"""TC03_PSDC_Study_Plco_Countries-UnitedStatesOfAmerica — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC03_PSDC_Study_Plco_Countries_UnitedStatesOfAmerica(psdc):
    psdc.load_query_file('TC03_PSDC_Study_Plco_Countries-UnitedStatesOfAmerica.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PLCO')
    psdc.select_filter('Studies/Countries', 'United States of America')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
