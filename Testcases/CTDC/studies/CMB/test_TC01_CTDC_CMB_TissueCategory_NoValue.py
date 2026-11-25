"""TC01_CTDC_CMB_TissueCategory-NoValue — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC01_CTDC_CMB_TissueCategory_NoValue(ctdc):
    ctdc.load_query_file('TC01_CTDC_CMB_TissueCategory-NoValue.xlsx')
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_study('CMB')
    ctdc.select_filter('Biospecimens/TissueCategory', 'NoValue')
    ctdc.read_statbar()
    ctdc.verify_tab('Participants')
    ctdc.verify_tab('Biospecimens')
    ctdc.verify_tab('Files')
    ctdc.verify_tab('Study Files')
    ctdc.assert_no_failures()
