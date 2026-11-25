"""TC07_PSDC_Study_Pbcs_Ethnicity-NotHispanicOrLatino — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC07_PSDC_Study_Pbcs_Ethnicity_NotHispanicOrLatino(psdc):
    psdc.load_query_file('TC07_PSDC_Study_Pbcs_Ethnicity-NotHispanicOrLatino.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Participants/Ethnicity', 'not hispanic or latino')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
