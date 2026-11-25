"""TC08_PSDC_Study_Pbcs_Sex-Female — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC08_PSDC_Study_Pbcs_Sex_Female(psdc):
    psdc.load_query_file('TC08_PSDC_Study_Pbcs_Sex-Female.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Participants/Sex', 'female')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
