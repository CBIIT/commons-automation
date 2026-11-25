"""TC06_PSDC_Study_Nlst_Ethnicity-HispanicOrLatino — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC06_PSDC_Study_Nlst_Ethnicity_HispanicOrLatino(psdc):
    psdc.load_query_file('TC06_PSDC_Study_Nlst_Ethnicity-HispanicOrLatino.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('NLST')
    psdc.select_filter('Participants/Ethnicity', 'hispanic or latino')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
